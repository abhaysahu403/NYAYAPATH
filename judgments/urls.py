from django.urls import path
from . import views

urlpatterns = [
    path("", views.JudgmentListView.as_view(), name="judgment-list"),
    path("search/", views.JudgmentSearchView.as_view(), name="judgment-search"),
    path("<uuid:pk>/", views.JudgmentDetailView.as_view(), name="judgment-detail"),
]
