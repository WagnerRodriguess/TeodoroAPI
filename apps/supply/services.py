from django.shortcuts import get_object_or_404

from apps.supply.models import Supply

class SupplyServices:

    @staticmethod
    def list_all():
        return Supply.objects.select_related("supply_label").all()

    @staticmethod
    def get(pk):
        return get_object_or_404(
            Supply.objects.select_related("supply_label"),
            pk=pk,
        )

    @staticmethod
    def create(validated_data):
        supply = Supply(**validated_data)
        supply.full_clean()
        supply.save()
        return supply

    @staticmethod
    def update(instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.full_clean()
        instance.save()
        return instance

    @staticmethod
    def delete(pk):
        supply = get_object_or_404(Supply, pk=pk)
        supply.delete()