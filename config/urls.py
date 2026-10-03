from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView

handler404 = "core.error_views.json_404"
handler500 = "core.error_views.json_500"

api_v1 = [
    path("", include("core.urls")),
    path("auth/", include("users.urls")),
    path("courts/", include("courts.urls")),
    path("sources/", include("sources.urls")),
    path("cases/", include("cases.urls")),
    path("judgments/", include("judgments.urls")),
    path("documents/", include("documents.urls")),
    path("ai/", include("ai.urls")),
    path("action-plans/", include("action_plans.urls")),
    path("drafts/", include("drafts.urls")),
    path("audit-logs/", include("audit.urls")),
    path("schema/", SpectacularAPIView.as_view(), name="schema"),
    path("docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
]

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/", include(api_v1)),
]
