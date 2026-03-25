from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from django.http import Http404

from apps.medical_supply_label.serializers import MedicalSupplyLabelSerializer
from apps.medical_supply_label.services import MedicalSupplyLabelServices


class MedicalSupplyLabelListAPIView(APIView):

    def get(self, request):
        supply_labels = MedicalSupplyLabelServices.list_all()
        serializer = MedicalSupplyLabelSerializer(supply_labels, many=True)
        return Response({"data": serializer.data}, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = MedicalSupplyLabelSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        supply_label = MedicalSupplyLabelServices.create(serializer.validated_data)
        response = MedicalSupplyLabelSerializer(supply_label)

        return Response({"data": response.data}, status=status.HTTP_201_CREATED)


class MedicalSupplyLabelDetailAPIView(APIView):

    def get(self, request, pk):
        try:
            supply_label_model = MedicalSupplyLabelServices.get(pk)
            serializer = MedicalSupplyLabelSerializer(supply_label_model)
            return Response({"data": serializer.data}, status=status.HTTP_200_OK)

        except Http404:
            return Response(
                {"error": "Supply Label not found"}, status=status.HTTP_404_NOT_FOUND
            )

    def patch(self, request, pk):

        try:
            supply_label = MedicalSupplyLabelServices.get(pk=pk)
            serializer = MedicalSupplyLabelSerializer(
                supply_label, data=request.data, partial=True
            )
            serializer.is_valid(raise_exception=True)

            updated = MedicalSupplyLabelServices.update(
                instance=supply_label, validated_data=serializer.validated_data
            )
            response = MedicalSupplyLabelSerializer(updated)

            return Response({"data": response.data}, status=status.HTTP_200_OK)

        except Http404:
            return Response(
                {"error": "Supply Label not found"}, status=status.HTTP_404_NOT_FOUND
            )

    def delete(self, request, pk):
        try:
            MedicalSupplyLabelServices.delete(pk=pk)
            return Response(status=status.HTTP_204_NO_CONTENT)

        except Http404:
            return Response(
                {"error": "Supply Label not found"}, status=status.HTTP_404_NOT_FOUND
            )
