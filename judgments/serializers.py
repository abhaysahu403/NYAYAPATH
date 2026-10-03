from rest_framework import serializers

from courts.serializers import CourtSerializer
from .models import Judgment, LegalTopic


class JudgmentSerializer(serializers.ModelSerializer):
    court_detail = CourtSerializer(source="court", read_only=True)

    class Meta:
        model = Judgment
        fields = ["id", "title", "court", "court_detail", "citation", "case_number", "judgment_date", "bench", "petitioner",
                  "respondent", "legal_topics", "summary", "source_url", "state", "district", "language", "keywords",
                  "verification_status", "is_demo_data", "created_at", "updated_at"]
        read_only_fields = fields


class JudgmentListSerializer(serializers.ModelSerializer):
    court_name = serializers.CharField(source="court.name", read_only=True, default=None)

    class Meta:
        model = Judgment
        fields = ["id", "title", "citation", "court_name", "judgment_date", "state", "legal_topics",
                  "verification_status", "is_demo_data"]
        read_only_fields = fields


class JudgmentSearchSerializer(serializers.Serializer):
    query = serializers.CharField(min_length=2, max_length=500)
    state = serializers.CharField(required=False, allow_blank=True)
    court = serializers.CharField(required=False, allow_blank=True)
    district = serializers.CharField(required=False, allow_blank=True)
    topic = serializers.ChoiceField(choices=[c for c, _ in LegalTopic.choices], required=False, allow_blank=True)
    date_from = serializers.DateField(required=False)
    date_to = serializers.DateField(required=False)
    language = serializers.ChoiceField(choices=["hi", "en"], required=False, allow_blank=True)
    source_type = serializers.CharField(required=False, allow_blank=True)
    judgments_only = serializers.BooleanField(required=False, default=True)

    def validate(self, attrs):
        if attrs.get("date_from") and attrs.get("date_to") and attrs["date_from"] > attrs["date_to"]:
            raise serializers.ValidationError("date_from must not be after date_to.")
        return attrs
