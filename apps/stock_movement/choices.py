from django.db import models
from django.utils.translation import gettext_lazy as _


class StockMovementType(models.TextChoices):
    ENTRY = "ENTRY", _("Entry")
    EXIT = "EXIT", _("Exit")
    ADJUSTMENT = "ADJUSTMENT", _("Adjustment")
