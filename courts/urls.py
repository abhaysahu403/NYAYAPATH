from django.urls import path
from . import views

urlpatterns = [
    path("", views.CourtListView.as_view(), name="court-list"),
    path("<uuid:pk>/", views.CourtDetailView.as_view(), name="court-detail"),
]
