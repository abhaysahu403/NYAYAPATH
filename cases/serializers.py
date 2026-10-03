from rest_framework import serializers
from .models import Case, CaseParty, CaseEvent, Hearing
from courts.serializers import CourtSerializer


class CasePartySerializer(serializers.ModelSerializer):
    class Meta:
        model = CaseParty
        fields = ["id", "party_type", "name", "advocate"]
        read_only_fields = ["id"]


class CaseEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = CaseEvent
        fields = ["id", "event_type", "event_date", "title", "description", "source_url", "data_origin", "created_at"]
        read_only_fields = ["id", "created_at"]


class HearingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Hearing
        fields = ["id", "hearing_date", "purpose", "result", "next_date", "judge"]
        read_only_fields = ["id"]


class CaseSerializer(serializers.ModelSerializer):
    court_detail = CourtSerializer(source="court", read_only=True)
    parties = CasePartySerializer(many=True, read_only=True)
    events = CaseEventSerializer(many=True, read_only=True)
    hearings = HearingSerializer(many=True, read_only=True)

    class Meta:
        model = Case
        fields = ["id", "cnr_number", "case_number", "case_type", "case_title", "court", "court_detail",
                  "state", "district", "filing_year", "filing_date", "status", "current_stage",
                  "last_hearing_date", "next_hearing_date", "description", "notes",
                  "data_origin", "is_demo_data",
                  "parties", "events", "hearings", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at", "data_origin"]


class CaseCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Case
        fields = ["cnr_number", "case_number", "case_type", "case_title", "court",
                  "state", "district", "filing_year", "filing_date", "status",
                  "current_stage", "last_hearing_date", "next_hearing_date", "description", "notes"]

    def create(self, validated_data):
        validated_data["user"] = self.context["request"].user
        return super().create(validated_data)


class CaseSearchSerializer(serializers.Serializer):
    cnr = serializers.CharField(required=False, allow_blank=True)
    case_number = serializers.CharField(required=False, allow_blank=True)
    case_type = serializers.CharField(required=False, allow_blank=True)
    status = serializers.CharField(required=False, allow_blank=True)
    state = serializers.CharField(required=False, allow_blank=True)
    district = serializers.CharField(required=False, allow_blank=True)
    year = serializers.IntegerField(required=False, min_value=1900)
    q = serializers.CharField(required=False, allow_blank=True)
