from django.urls import path
from . import views

urlpatterns = [
    path("", views.DraftListView.as_view(), name="draft-list"),
    path("case-summary/", views.CaseSummaryView.as_view(), name="draft-case-summary"),
    path("lawyer-brief/", views.LawyerBriefView.as_view(), name="draft-lawyer-brief"),
    path("rti/", views.RTIDraftView.as_view(), name="draft-rti"),
    path("<uuid:pk>/", views.DraftDetailView.as_view(), name="draft-detail"),
]
