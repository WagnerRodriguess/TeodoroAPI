from django.urls import path

from apps.medical_supply_label.views import (
    MedicalSupplyLabelListAPIView,
    MedicalSupplyLabelDetailAPIView,
)

app_name = "medical_supply_label"

urlpatterns = [
    path("", MedicalSupplyLabelListAPIView.as_view(), name="medical_supply_label_list"),
    path(
        "<int:pk>/",
        MedicalSupplyLabelDetailAPIView.as_view(),
        name="medical_supply_label_detail",
    ),
]
