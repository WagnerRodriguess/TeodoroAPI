from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import (
    extend_schema,
    extend_schema_view,
    OpenApiResponse,
)

from apps.supply.services import SupplyServices
from apps.supply.serializers import SupplySerializer
from apps.account.permissions import IsNotCustomer


# ── Supply views ──────────────────────────────────────────────────────────────

@extend_schema(tags=["supplies"])
@extend_schema_view(
    get=extend_schema(
        operation_id="supplies_list",
        summary="List supplies",
        description="Returns all supplies registered in the system.",
        responses={
            401: OpenApiResponse(description="Authentication credentials were not provided."),
        },
    ),
    post=extend_schema(
        operation_id="supplies_create",
        summary="Create supply",
        description="Creates a new supply entry. Restricted to non-customer users.",
        request=SupplySerializer,
        responses={
            400: OpenApiResponse(description="Validation error."),
            401: OpenApiResponse(description="Authentication credentials were not provided."),
            403: OpenApiResponse(description="Customers cannot access this resource."),
        },
    ),
)
class SupplyListAPIView(APIView):
    serializer_class = SupplySerializer

    def get_permissions(self):
        if self.request.method == "POST":
            return [IsAuthenticated(), IsNotCustomer()]
        return [IsAuthenticated()]

    def get(self, request):
        supplies = SupplyServices.list_all()
        serializer = SupplySerializer(supplies, many=True)
        return Response({"data": serializer.data}, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = SupplySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        supply = SupplyServices.create(serializer.validated_data)
        response = SupplySerializer(supply)
        return Response({"data": response.data}, status=status.HTTP_201_CREATED)


@extend_schema(tags=["supplies"])
@extend_schema_view(
    get=extend_schema(
        operation_id="supplies_retrieve",
        summary="Retrieve supply",
        responses={
            401: OpenApiResponse(description="Authentication credentials were not provided."),
            404: OpenApiResponse(description="Supply not found."),
        },
    ),
    patch=extend_schema(
        operation_id="supplies_partial_update",
        summary="Partially update supply",
        request=SupplySerializer,
        responses={
            400: OpenApiResponse(description="Validation error."),
            401: OpenApiResponse(description="Authentication credentials were not provided."),
            403: OpenApiResponse(description="Customers cannot access this resource."),
            404: OpenApiResponse(description="Supply not found."),
        },
    ),
    delete=extend_schema(
        operation_id="supplies_destroy",
        summary="Delete supply",
        responses={
            204: OpenApiResponse(description="Supply deleted."),
            401: OpenApiResponse(description="Authentication credentials were not provided."),
            403: OpenApiResponse(description="Customers cannot access this resource."),
            404: OpenApiResponse(description="Supply not found."),
        },
    ),
)
class SupplyDetailAPIView(APIView):
    serializer_class = SupplySerializer

    def get_permissions(self):
        if self.request.method in ("PATCH", "DELETE"):
            return [IsAuthenticated(), IsNotCustomer()]
        return [IsAuthenticated()]

    def get(self, request, pk):
        
        supply = SupplyServices.get(pk)
        serializer = SupplySerializer(supply)
        return Response({"data": serializer.data}, status=status.HTTP_200_OK)

    def patch(self, request, pk):
       
        supply = SupplyServices.get(pk)
        serializer = SupplySerializer(supply, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        updated = SupplyServices.update(supply, serializer.validated_data)
        response = SupplySerializer(updated)
        return Response({"data": response.data}, status=status.HTTP_200_OK)

    def delete(self, request, pk):
       
        SupplyServices.delete(pk) 
        return Response(status=status.HTTP_204_NO_CONTENT)