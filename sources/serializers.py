from rest_framework import serializers
from .models import Source


class SourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Source
        fields = ["id", "source_type", "title", "url", "court", "publication_date", "retrieved_at",
                  "identifier", "verification_status", "is_demo_data", "created_at"]
        read_only_fields = ["id", "retrieved_at", "created_at"]
