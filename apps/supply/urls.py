from django.urls import path

from apps.supply.views import (
    SupplyListAPIView,
    SupplyDetailAPIView,
)

app_name = "supply"

urlpatterns = [
    # Supplies
    path("", SupplyListAPIView.as_view(), name="supply_list"),
    path("<int:pk>/", SupplyDetailAPIView.as_view(), name="supply_detail"),
]