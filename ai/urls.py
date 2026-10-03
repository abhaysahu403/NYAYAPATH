from django.urls import path
from . import views

urlpatterns = [
    path("chat/", views.ChatView.as_view(), name="ai-chat"),
    path("conversations/", views.ConversationListView.as_view(), name="ai-conversations"),
    path("conversations/<uuid:pk>/", views.ConversationDetailView.as_view(), name="ai-conversation-detail"),
    path("judgments/<uuid:pk>/explain/", views.JudgmentExplainView.as_view(), name="ai-judgment-explain"),
    path("similar-cases/", views.SimilarCasesView.as_view(), name="ai-similar-cases"),
    path("responses/<uuid:pk>/feedback/", views.ResponseFeedbackView.as_view(), name="ai-response-feedback"),
]
