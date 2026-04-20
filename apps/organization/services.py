from django.db import transaction
from django.shortcuts import get_object_or_404
from apps.organization.models import Organization


class OrganizationServices:
    @staticmethod
    def list_all():
        return Organization.objects.all()

    @staticmethod
    def get(pk):
        return get_object_or_404(Organization, pk=pk)

    @staticmethod
    @transaction.atomic
    def create(validated_data):
        organization = Organization(**dict(validated_data))
        organization.full_clean()
        organization.save()
        return organization

    @staticmethod
    @transaction.atomic
    def update(instance, validated_data):
        for attr, value in dict(validated_data).items():
            setattr(instance, attr, value)
        instance.full_clean()
        instance.save()
        return instance

    @staticmethod
    @transaction.atomic
    def delete(pk):
        organization = get_object_or_404(Organization, pk=pk)
        organization.delete()
