from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

system_patterns = [
    path("schema/", SpectacularAPIView.as_view(), name="schema"),
    path("docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
]

api_patterns = [
    path("authentication/", include("apps.authentication.urls")),
    path("supply-labels/", include("apps.supply_label.urls")),
    path("accounts/", include("apps.account.urls")),
    path("organizations/", include("apps.organization.urls")),
]

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include(api_patterns)),
    path("system/", include(system_patterns)),
]
