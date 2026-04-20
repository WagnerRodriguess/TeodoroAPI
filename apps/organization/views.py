from django.http import Http404
from rest_framework import status, serializers
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from drf_spectacular.utils import (
    extend_schema,
    extend_schema_view,
    inline_serializer,
    OpenApiExample,
    OpenApiResponse,
)
from apps.account.permissions import IsNotCustomer
from apps.organization.serializers import OrganizationSerializer
from apps.organization.services import OrganizationServices


OrganizationEnvelopeSerializer = inline_serializer(
    name="OrganizationEnvelope",
    fields={"data": OrganizationSerializer()},
)

OrganizationListEnvelopeSerializer = inline_serializer(
    name="OrganizationListEnvelope",
    fields={"data": OrganizationSerializer(many=True)},
)

ErrorResponseSerializer = inline_serializer(
    name="OrganizationErrorResponse",
    fields={"error": serializers.CharField()},
)


@extend_schema(tags=["organizations"])
@extend_schema_view(
    get=extend_schema(
        operation_id="organizations_list",
        summary="List organizations",
        description=(
            "Returns every organization registered in the system, wrapped "
            "in a `data` envelope. Open to any client — authentication is "
            "not required."
        ),
        responses={200: OrganizationListEnvelopeSerializer},
        auth=None
    ),
    post=extend_schema(
        operation_id="organizations_create",
        summary="Create organization",
        description=(
            "Creates a new `Organization`. Restricted to authenticated "
            "non-customer users."
        ),
        request=OrganizationSerializer,
        responses={
            201: OrganizationEnvelopeSerializer,
            400: OpenApiResponse(
                description="Validation error (invalid CNPJ, duplicated CNPJ, etc.)."
            ),
            401: OpenApiResponse(
                description="Authentication credentials were not provided."
            ),
            403: OpenApiResponse(
                description="Authenticated user is a customer and cannot create organizations."
            ),
        },
        examples=[
            OpenApiExample(
                "Valid organization payload",
                value={
                    "name": "Hospital Teodoro",
                    "cnpj": "11.222.333/0001-81",
                    "address": "Av. Paulista, 1000",
                    "phone_number": "(11) 91234-5678",
                },
                request_only=True,
            ),
        ],
    ),
)
class OrganizationListAPIView(APIView):
    serializer_class = OrganizationSerializer

    def get_permissions(self):
        if self.request.method == "GET":
            return [AllowAny()]
        return [IsAuthenticated(), IsNotCustomer()]

    def get(self, request):
        organizations = OrganizationServices.list_all()
        serializer = OrganizationSerializer(organizations, many=True)
        return Response({"data": serializer.data}, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = OrganizationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        organization = OrganizationServices.create(serializer.validated_data)
        response = OrganizationSerializer(organization)
        return Response(
            {"message": "Organization created successfully.", "data": response.data},
            status=status.HTTP_201_CREATED,
        )


@extend_schema(tags=["organizations"])
@extend_schema_view(
    get=extend_schema(
        operation_id="organizations_retrieve",
        summary="Retrieve organization",
        description=(
            "Returns a single organization identified by its primary key. "
            "Open to any client — authentication is not required."
        ),
        responses={
            200: OrganizationEnvelopeSerializer,
            404: OpenApiResponse(
                response=ErrorResponseSerializer,
                description="Organization not found.",
            ),
        },
        auth=None,
    ),
    patch=extend_schema(
        operation_id="organizations_partial_update",
        summary="Partially update organization",
        description=(
            "Updates any subset of fields on an existing `Organization`. "
            "Restricted to authenticated non-customer users."
        ),
        request=OrganizationSerializer,
        responses={
            200: OrganizationEnvelopeSerializer,
            400: OpenApiResponse(description="Validation error."),
            401: OpenApiResponse(
                description="Authentication credentials were not provided."
            ),
            403: OpenApiResponse(
                description="Authenticated user is a customer and cannot update organizations."
            ),
            404: OpenApiResponse(
                response=ErrorResponseSerializer,
                description="Organization not found.",
            ),
        },
    ),
    delete=extend_schema(
        operation_id="organizations_destroy",
        summary="Delete organization",
        description=(
            "Hard-deletes an organization. Restricted to authenticated "
            "non-customer users."
        ),
        responses={
            204: OpenApiResponse(description="Organization deleted."),
            401: OpenApiResponse(
                description="Authentication credentials were not provided."
            ),
            403: OpenApiResponse(
                description="Authenticated user is a customer and cannot delete organizations."
            ),
            404: OpenApiResponse(
                response=ErrorResponseSerializer,
                description="Organization not found.",
            ),
        },
    ),
)
class OrganizationDetailAPIView(APIView):
    serializer_class = OrganizationSerializer

    def get_permissions(self):
        if self.request.method == "GET":
            return [AllowAny()]
        return [IsAuthenticated(), IsNotCustomer()]

    def get(self, request, pk):
        try:
            organization = OrganizationServices.get(pk)
        except Http404:
            return Response(
                {"error": "Organization not found"},
                status=status.HTTP_404_NOT_FOUND,
            )
        serializer = OrganizationSerializer(organization)
        return Response({"data": serializer.data}, status=status.HTTP_200_OK)

    def patch(self, request, pk):
        try:
            organization = OrganizationServices.get(pk)
        except Http404:
            return Response(
                {"error": "Organization not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = OrganizationSerializer(
            organization, data=request.data, partial=True
        )
        serializer.is_valid(raise_exception=True)

        updated = OrganizationServices.update(organization, serializer.validated_data)
        response = OrganizationSerializer(updated)
        return Response({"data": response.data}, status=status.HTTP_200_OK)

    def delete(self, request, pk):
        try:
            OrganizationServices.delete(pk)
        except Http404:
            return Response(
                {"error": "Organization not found"},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response(status=status.HTTP_204_NO_CONTENT)
