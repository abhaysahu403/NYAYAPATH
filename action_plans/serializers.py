from rest_framework import serializers
from .models import ActionPlan, ActionStep


class ActionStepSerializer(serializers.ModelSerializer):
    class Meta:
        model = ActionStep
        fields = ["id", "step_number", "title", "description", "why_relevant",
                  "documents_needed", "legal_basis", "estimated_timeline",
                  "difficulty", "source_references", "kind", "source_backed",
                  "status", "completed_at"]
        read_only_fields = ["id", "completed_at"]


class ActionPlanSerializer(serializers.ModelSerializer):
    steps = ActionStepSerializer(many=True, read_only=True)

    class Meta:
        model = ActionPlan
        fields = ["id", "title", "situation_assessment", "delay_cause_analysis",
                  "immediate_priority", "warnings", "supporting_sources",
                  "original_query", "language", "status", "disclaimer",
                  "steps", "created_at", "updated_at"]
        read_only_fields = fields


class ActionPlanGenerateSerializer(serializers.Serializer):
    message = serializers.CharField(min_length=5, max_length=2000)
    language = serializers.ChoiceField(choices=["hi", "en"], default="hi")
    case_id = serializers.UUIDField(required=False, allow_null=True)
    conversation_id = serializers.UUIDField(required=False, allow_null=True)
