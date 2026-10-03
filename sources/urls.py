from django.urls import path
from . import views

urlpatterns = [
    path("", views.SourceListView.as_view(), name="source-list"),
    path("<uuid:pk>/", views.SourceDetailView.as_view(), name="source-detail"),
]
