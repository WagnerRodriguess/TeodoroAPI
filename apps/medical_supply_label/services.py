from django.shortcuts import get_object_or_404

from .models import MedicalSupplyLabel


class MedicalSupplyLabelServices:

    @staticmethod
    def list_all():
        return MedicalSupplyLabel.objects.all()

    @staticmethod
    def get(pk):
        return get_object_or_404(MedicalSupplyLabel, pk=pk)

    @staticmethod
    def create(validated_data):
        return MedicalSupplyLabel.objects.create(**validated_data)

    @staticmethod
    def update(instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance

    @staticmethod
    def delete(pk):
        supply_label = get_object_or_404(MedicalSupplyLabel, pk=pk)
        supply_label.delete()
