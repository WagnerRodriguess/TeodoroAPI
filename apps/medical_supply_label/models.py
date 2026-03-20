from django.db import models
from django.utils.translation import gettext_lazy as _

from .validators import validate_category, validate_not_blank, validate_supply_type

# Create your models here.

MEDICAL_SUPPLY_TYPES = [
    ("medication", _("Medication")),
    ("equipment", _("Equipment")),
    ("sterilization", _("Sterilization")),
    ("nutrition", _("Nutrition")),
    ("blood_product", _("Blood Product")),
    ("other", _("Other")),
]

MEDICAL_SUPPLY_CATEGORIES = [
    ("disposable", _("Disposable")),
    ("reusable", _("Reusable")),
    ("implantable", _("Implantable")),
    ("diagnostic", _("Diagnostic")),
    ("therapeutic", _("Therapeutic")),
    ("other", _("Other")),
]


class MedicalSupplyLabel(models.Model):
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
