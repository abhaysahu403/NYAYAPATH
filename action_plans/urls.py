from django.urls import path
from . import views

urlpatterns = [
    path("", views.ActionPlanListView.as_view(), name="action-plan-list"),
    path("generate/", views.ActionPlanGenerateView.as_view(), name="action-plan-generate"),
    path("<uuid:pk>/", views.ActionPlanDetailView.as_view(), name="action-plan-detail"),
    path("<uuid:pk>/steps/<uuid:step_id>/complete/", views.ActionStepCompleteView.as_view(), name="action-step-complete"),
]
