from django.urls import path
from . import views

urlpatterns = [
    path("", views.AuditLogView.as_view(), name="audit-log"),
]
