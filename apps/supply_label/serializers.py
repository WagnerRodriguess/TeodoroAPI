from rest_framework import serializers

from apps.supply_label.models import SupplyLabel

from apps.supply_label.validators import (
    validate_category,
    validate_supply_type,
)


class SupplyLabelSerializer(serializers.ModelSerializer):

    id = serializers.IntegerField(read_only=True)

    def validate_supply_type(self, value):
        validate_supply_type(value)
        return value

    def validate_category(self, value):
        validate_category(value)
        return value

    class Meta:
        model = SupplyLabel
        fields = ["id", "name", "supply_label_type", "category", "details"]
