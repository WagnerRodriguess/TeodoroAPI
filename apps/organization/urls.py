from django.urls import path

from apps.organization.views import (
    OrganizationDetailAPIView,
    OrganizationListAPIView,
)

app_name = "organization"

urlpatterns = [
    path("", OrganizationListAPIView.as_view(), name="organization_list"),
    path(
        "<int:pk>/",
        OrganizationDetailAPIView.as_view(),
        name="organization_detail",
    ),
]
