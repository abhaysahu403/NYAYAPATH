"""Document API: upload, list, detail, delete, analyze, ask, expiring download links. Ownership enforced everywhere."""
import logging

from django.conf import settings
from django.core import signing
from django.http import FileResponse
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from ai.models import AIRequestType
from ai.providers.factory import get_ai_provider
from ai.schemas import DocumentAnalysis
from ai.services.citation_verification import CitationVerificationService
from ai.services.grounded_answer import GroundedAnswerService
from ai.services.retrieval_context import evidence_from_document_chunks
from ai.services.safety import LegalSafetyService
from ai.services.tracking import AICall
from audit import services as audit_svc
from audit.models import AuditEventType
from core.exceptions import NotFoundError, PermissionDeniedError, ValidationError
from core.pagination import StandardPagination
from core.throttles import AIDocumentThrottle
from legal_research.services.search import search_document_chunks
from .models import Document, DocumentChunk, DocumentStatus
from .processing import compute_checksum, process_document, validate_upload
from .serializers import DocumentAskSerializer, DocumentSerializer, DocumentUploadSerializer
from .storage import absolute_path, delete_file, file_exists, save_upload

logger = logging.getLogger("nyayapath.documents")
LINK_SALT = "nyayapath.document-download"


def _get_doc(pk, user) -> Document:
    """404 for unknown ids; 403 when the document belongs to someone else (admins excluded: documents are private)."""
    try:
        doc = Document.objects.get(pk=pk)
    except Document.DoesNotExist:
        raise NotFoundError("Document not found.", code="DOCUMENT_NOT_FOUND")
    if doc.owner_id != user.id:
        raise PermissionDeniedError()
    return doc


class DocumentListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        qs = Document.objects.filter(owner=request.user)
        if request.query_params.get("status"):
            qs = qs.filter(status=request.query_params["status"].upper())
        if request.query_params.get("case"):
            qs = qs.filter(case_id=request.query_params["case"])
        paginator = StandardPagination()
        page = paginator.paginate_queryset(qs, request)
        return paginator.get_paginated_response(DocumentSerializer(page, many=True).data)


class DocumentUploadView(APIView):
    permission_classes = [IsAuthenticated]
    throttle_classes = [AIDocumentThrottle]

    def post(self, request):
        ser = DocumentUploadSerializer(data=request.data, context={"request": request})
        if not ser.is_valid():
            raise ValidationError(detail=ser.errors)
        f = ser.validated_data["file"]
        try:
            mime = validate_upload(f)
        except ValueError as exc:
            raise ValidationError(str(exc), code="INVALID_FILE")
        checksum = compute_checksum(f)
        stored_name, rel_path = save_upload(f, str(request.user.id))
        doc = Document.objects.create(
            owner=request.user, original_filename=f.name[:500], stored_filename=stored_name, file_path=rel_path,
            mime_type=mime, file_size=f.size, case=ser.validated_data.get("case"), checksum=checksum)
        audit_svc.record(AuditEventType.DOCUMENT_UPLOADED, request=request, resource_type="Document", resource_id=doc.id,
                         description="Document uploaded", metadata={"mime": mime, "size": f.size})
        if settings.DOCUMENT_PROCESSING_MODE == "sync":
            process_document(str(doc.id))
            doc.refresh_from_db()
        return Response(DocumentSerializer(doc).data, status=status.HTTP_201_CREATED)


class DocumentDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        doc = _get_doc(pk, request.user)
        audit_svc.record(AuditEventType.DOCUMENT_ACCESSED, request=request, resource_type="Document", resource_id=pk)
        data = DocumentSerializer(doc).data
        if request.query_params.get("include_text") in {"1", "true"}:
            data["extracted_text"] = doc.extracted_text
        return Response(data)

    def delete(self, request, pk):
        doc = _get_doc(pk, request.user)
        delete_file(doc.file_path)  # secure deletion: file first, then rows (chunks cascade)
        audit_svc.record(AuditEventType.DOCUMENT_DELETED, request=request, resource_type="Document", resource_id=pk,
                         description="Document deleted")
        doc.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class DocumentReprocessView(APIView):
    """Retry processing (e.g. after OCR was installed)."""
    permission_classes = [IsAuthenticated]
    throttle_classes = [AIDocumentThrottle]

    def post(self, request, pk):
        doc = _get_doc(pk, request.user)
        process_document(str(doc.id))
        doc.refresh_from_db()
        return Response(DocumentSerializer(doc).data)


class DocumentAnalyzeView(APIView):
    permission_classes = [IsAuthenticated]
    throttle_classes = [AIDocumentThrottle]

    def post(self, request, pk):
        doc = _get_doc(pk, request.user)
        if doc.status in (DocumentStatus.UPLOADED, DocumentStatus.PROCESSING):
            raise ValidationError("The document is still being processed.", code="DOCUMENT_NOT_READY")
        if doc.status in (DocumentStatus.FAILED, DocumentStatus.OCR_REQUIRED) or not doc.extracted_text:
            raise ValidationError("No readable text is available for this document.", code="DOCUMENT_NO_TEXT")
        lang = request.data.get("language") or request.user.preferred_language or "en"
        lang = "hi" if lang == "hi" else "en"

        budget, passages = settings.DOCUMENT_ANALYSIS_MAX_CHARS, []
        for i, c in enumerate(DocumentChunk.objects.filter(document=doc).order_by("chunk_index"), 1):
            if budget <= 0:
                break
            passages.append({"label": f"S{i}", "text": c.text[:budget], "title": doc.original_filename,
                             "locator": f"p. {c.page_number}" if c.page_number else None, "citation": None})
            budget -= len(c.text)

        provider = get_ai_provider()
        call = AICall(request.user, AIRequestType.DOCUMENT_ANALYZE, provider, doc.original_filename)
        safety = LegalSafetyService()
        try:
            analysis = DocumentAnalysis.model_validate(provider.analyze_document(lang, passages).data)
        except Exception as exc:  # noqa: BLE001
            call.failure(type(exc).__name__)
            analysis = DocumentAnalysis(plain_summary=(doc.extracted_text or "")[:400])
            degraded = True
        else:
            degraded = False
        summary = safety.inspect(analysis.plain_summary, lang=lang, add_disclaimer=True)
        result = analysis.model_dump()
        result.update(plain_summary=summary.text, degraded=degraded, language=lang,
                      note=("AI-generated reading of YOUR uploaded document. It is not verified legal information."
                            if lang == "en" else "यह आपके अपलोड किए गए दस्तावेज़ का AI-निर्मित सार है; यह सत्यापित कानूनी जानकारी नहीं है।"))
        doc.analysis_result = result
        doc.status = DocumentStatus.ANALYZED
        doc.save(update_fields=["analysis_result", "status"])
        if not degraded:
            call.success(summary.text, lang, "user_document", {"document_id": str(doc.id)}, summary.flag_codes)
        audit_svc.record(AuditEventType.DOCUMENT_ANALYZED, request=request, resource_type="Document", resource_id=pk)
        return Response({"document_id": str(doc.id), "status": doc.status, "analysis": result})


class DocumentAskView(APIView):
    """Question answering over ONE of the user's own documents; answers cite page numbers."""
    permission_classes = [IsAuthenticated]
    throttle_classes = [AIDocumentThrottle]

    def post(self, request, pk):
        doc = _get_doc(pk, request.user)
        ser = DocumentAskSerializer(data=request.data)
        if not ser.is_valid():
            raise ValidationError(detail=ser.errors)
        question, lang = ser.validated_data["question"], ser.validated_data["language"]
        if doc.status in (DocumentStatus.UPLOADED, DocumentStatus.PROCESSING):
            raise ValidationError("The document is still being processed.", code="DOCUMENT_NOT_READY")
        chunks = search_document_chunks(request.user, question, document_ids=[doc.id], top_k=5)
        if not chunks:
            chunks = list(DocumentChunk.objects.select_related("document").filter(document=doc).order_by("chunk_index")[:3])
        evidence = evidence_from_document_chunks(chunks)
        provider = get_ai_provider()
        call = AICall(request.user, AIRequestType.DOCUMENT_ASK, provider, question)
        draft = GroundedAnswerService(provider).answer(question, lang, "", evidence)
        report = CitationVerificationService().verify(draft.answer, evidence, lang=lang,
                                                      claim_labels=[s for c in draft.claims for s in c.source_ids])
        safe = LegalSafetyService().inspect(report.answer, lang=lang, source_text=evidence.text_blob())
        payload = {"question_hash_only": True, "document_id": str(doc.id), "sources": report.sources}
        call.success(safe.text, lang, "user_document", payload, safe.flag_codes)
        return Response({
            "question": question, "answer": safe.text, "language": lang,
            "document": {"id": str(doc.id), "filename": doc.original_filename},
            "sources": [s for s in report.sources if s["cited"]] or report.sources,
            "unknowns": draft.unknowns,
            "verification_status": "from_user_document",
            "warnings": [f.as_dict() for f in safe.flags if f.code != "DISCLAIMER_ADDED"],
            "notice": ("Answer is based only on your uploaded document and is not verified legal information."
                       if lang == "en" else "उत्तर केवल आपके अपलोड किए दस्तावेज़ पर आधारित है; यह सत्यापित कानूनी जानकारी नहीं है।"),
        })


class DocumentDownloadLinkView(APIView):
    """Issue a short-lived signed link. The file itself is never exposed by a static/media URL."""
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        doc = _get_doc(pk, request.user)
        if not file_exists(doc.file_path):
            raise NotFoundError("The stored file is no longer available.", code="FILE_MISSING")
        token = signing.dumps({"doc": str(doc.id), "user": str(request.user.id)}, salt=LINK_SALT)
        audit_svc.record(AuditEventType.DOCUMENT_LINK_ISSUED, request=request, resource_type="Document", resource_id=pk)
        return Response({"url": request.build_absolute_uri(f"/api/v1/documents/download/{token}/"),
                         "expires_in_seconds": settings.DOCUMENT_LINK_TTL_SECONDS})


class DocumentDownloadView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def get(self, request, token):
        try:
            data = signing.loads(token, salt=LINK_SALT, max_age=settings.DOCUMENT_LINK_TTL_SECONDS)
            doc = Document.objects.get(pk=data["doc"], owner_id=data["user"])
        except (signing.BadSignature, Document.DoesNotExist, KeyError):
            raise NotFoundError("This download link is invalid or has expired.", code="LINK_EXPIRED")
        if not file_exists(doc.file_path):
            raise NotFoundError("The stored file is no longer available.", code="FILE_MISSING")
        audit_svc.record(AuditEventType.DOCUMENT_ACCESSED, request=request, user=doc.owner, resource_type="Document",
                         resource_id=doc.id, description="Downloaded via signed link")
        resp = FileResponse(open(absolute_path(doc.file_path), "rb"), as_attachment=True, filename=doc.original_filename,
                            content_type=doc.mime_type)
        resp["Cache-Control"] = "private, no-store"
        resp["X-Content-Type-Options"] = "nosniff"
        return resp
