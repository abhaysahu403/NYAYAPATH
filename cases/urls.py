from django.urls import path
from . import views

urlpatterns = [
    path("", views.CaseListCreateView.as_view(), name="case-list"),
    path("search/", views.CaseSearchView.as_view(), name="case-search"),
    path("<uuid:pk>/", views.CaseDetailView.as_view(), name="case-detail"),
    path("<uuid:pk>/timeline/", views.CaseTimelineView.as_view(), name="case-timeline"),
    path("<uuid:pk>/hearings/", views.CaseHearingView.as_view(), name="case-hearings"),
    path("<uuid:pk>/parties/", views.CasePartyView.as_view(), name="case-parties"),
]
