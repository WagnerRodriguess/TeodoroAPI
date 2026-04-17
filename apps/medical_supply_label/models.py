from django.db import models
from apps.core.models import TimeStampedModel
from django.utils.translation import gettext_lazy as _
from apps.medical_supply_label.validators import (
    validate_category,
    validate_not_blank,
    validate_supply_type,
)
from apps.medical_supply_label.choices import (
    MEDICAL_SUPPLY_TYPES,
    MEDICAL_SUPPLY_CATEGORIES,
)

class MedicalSupplyLabel(TimeStampedModel):
    name = models.CharField(
        max_length=200, verbose_name=_("name"), validators=[validate_not_blank]
    )
    supply_type = models.CharField(
        max_length=50,
        choices=MEDICAL_SUPPLY_TYPES,
        verbose_name=_("supply type"),
        validators=[validate_supply_type, validate_not_blank],
    )
    category = models.CharField(
        max_length=50,
        choices=MEDICAL_SUPPLY_CATEGORIES,
        verbose_name=_("category"),
        validators=[validate_not_blank, validate_category],
    )
    details = models.TextField(
        verbose_name=_("details"), validators=[validate_not_blank]
    )

    def __str__(self):
        return f"{self.name} - {self.details}"
