from rest_framework import serializers
from apps.organization.models import Organization
from apps.core.validators import validate_cnpj, validate_phone_number


class OrganizationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organization
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]

    def validate_cnpj(self, value):
        validate_cnpj(value)
        return value

    def validate_phone_number(self, value):
        validate_phone_number(value)
        return value
