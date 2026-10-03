from rest_framework import serializers
from .models import Document, DocumentChunk


class DocumentSerializer(serializers.ModelSerializer):
    chunks_count = serializers.SerializerMethodField()

    class Meta:
        model = Document
        fields = [
            "id", "original_filename", "mime_type", "file_size", "status",
            "page_count", "ocr_performed", "case", "uploaded_at", "processed_at",
            "chunks_count", "analysis_result",
        ]
        read_only_fields = fields

    def get_chunks_count(self, obj):
        return obj.chunks.count()


class DocumentUploadSerializer(serializers.Serializer):
    file = serializers.FileField()
    case = serializers.UUIDField(required=False, allow_null=True)

    def validate_case(self, value):
        if value is None:
            return None
        from cases.models import Case
        try:
            return Case.objects.get(pk=value, user=self.context["request"].user)
        except Case.DoesNotExist:
            raise serializers.ValidationError("Case not found or access denied.")


class DocumentAskSerializer(serializers.Serializer):
    question = serializers.CharField(min_length=3, max_length=500)
    language = serializers.ChoiceField(choices=["hi", "en"], default="en")
