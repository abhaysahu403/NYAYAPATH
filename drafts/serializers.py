from rest_framework import serializers
from .models import GeneratedDraft, DraftType


class DraftSerializer(serializers.ModelSerializer):
    class Meta:
        model = GeneratedDraft
        fields = [
            "id", "draft_type", "title", "content_english", "content_hindi",
            "language", "placeholders_used", "field_provenance", "source_references",
            "filing_instructions", "important_notes", "disclaimer",
            "created_at", "updated_at",
        ]
        read_only_fields = fields


class CaseSummaryRequestSerializer(serializers.Serializer):
    case_id = serializers.UUIDField(required=False, allow_null=True)
    message = serializers.CharField(min_length=5, max_length=3000)
    language = serializers.ChoiceField(choices=["hi", "en"], default="hi")


class LawyerBriefRequestSerializer(serializers.Serializer):
    case_id = serializers.UUIDField(required=False, allow_null=True)
    message = serializers.CharField(min_length=5, max_length=3000)
    language = serializers.ChoiceField(choices=["hi", "en"], default="hi")
    lawyer_name = serializers.CharField(required=False, allow_blank=True, max_length=200, default="")
    court_name = serializers.CharField(required=False, allow_blank=True, max_length=200, default="")


class RTIRequestSerializer(serializers.Serializer):
    case_id = serializers.UUIDField(required=False, allow_null=True)
    message = serializers.CharField(min_length=5, max_length=3000)
    language = serializers.ChoiceField(choices=["hi", "en"], default="hi")
    applicant_name = serializers.CharField(required=False, allow_blank=True, max_length=200, default="")
    public_authority = serializers.CharField(required=False, allow_blank=True, max_length=300, default="")
    information_sought = serializers.CharField(required=False, allow_blank=True, max_length=1000, default="")
