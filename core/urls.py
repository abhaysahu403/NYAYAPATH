from django.urls import path
from core.views import HealthView, LegalTopicListView

urlpatterns = [
    path("health/", HealthView.as_view(), name="health"),
    path("legal-topics/", LegalTopicListView.as_view(), name="legal-topics"),
]
