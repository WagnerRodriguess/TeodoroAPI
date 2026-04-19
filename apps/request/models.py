from django.db import models
from .choices import REQUEST_TYPES
from apps.supply.models import Supply
from django.contrib.auth.models import User
from apps.core.models import TimeStampedModel


class Request(TimeStampedModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="request")
    request_type = models.CharField(
        max_length=20,
        choices=REQUEST_TYPES,
    )
    supply = models.ForeignKey(Supply, on_delete=models.PROTECT, related_name="request")
    description = models.TextField(max_length=100)
    is_approved = models.BooleanField(default=False)
    approval_date = models.DateField(null=True, blank=True)
    quantity = models.FloatField()

    def _str_(self):
        return f"{self.request_type}"
