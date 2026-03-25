from rest_framework import serializers

from apps.medical_supply_label.models import MedicalSupplyLabel

from apps.medical_supply_label.validators import (
    validate_category,
    validate_not_blank,
    validate_supply_type,
)


class MedicalSupplyLabelSerializer(serializers.ModelSerializer):

    id = serializers.IntegerField(read_only=True)

    def validate_name(self, value):
        validate_not_blank(value)
        return value

    def validate_supply_type(self, value):
        validate_supply_type(value)
        return value

    def validate_category(self, value):
        validate_category(value)
        return value

    def validate_details(self, value):
        validate_not_blank(value)
        return value

    class Meta:
        model = MedicalSupplyLabel
        fields = ["id", "name", "supply_type", "category", "details"]
