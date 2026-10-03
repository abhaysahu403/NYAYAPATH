from django.urls import path
from . import views

urlpatterns = [
    path("", views.DocumentListView.as_view(), name="document-list"),
    path("upload/", views.DocumentUploadView.as_view(), name="document-upload"),
    path("download/<str:token>/", views.DocumentDownloadView.as_view(), name="document-download"),
    path("<uuid:pk>/", views.DocumentDetailView.as_view(), name="document-detail"),
    path("<uuid:pk>/analyze/", views.DocumentAnalyzeView.as_view(), name="document-analyze"),
    path("<uuid:pk>/ask/", views.DocumentAskView.as_view(), name="document-ask"),
    path("<uuid:pk>/reprocess/", views.DocumentReprocessView.as_view(), name="document-reprocess"),
    path("<uuid:pk>/download-link/", views.DocumentDownloadLinkView.as_view(), name="document-download-link"),
]
