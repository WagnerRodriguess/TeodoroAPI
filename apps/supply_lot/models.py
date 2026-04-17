from django.db import models
from apps.core.models import TimeStampedModel
from django.utils.translation import gettext_lazy as _
from apps.supply_lot.choices import SUPPLY_LOT_STATUSES
from apps.supply_lot.validators import (
    validate_manufacturing_before_expiration,
    validate_status,
)


class SupplyLot(TimeStampedModel):
    status = models.CharField(
        max_length=20,
        choices=SUPPLY_LOT_STATUSES,
        default="pending",
        verbose_name=_("status"),
        validators=[validate_status],
    )
    inspection = models.OneToOneField(
        "inspection.Inspection",
        on_delete=models.PROTECT,
        related_name="supply_lot",
        verbose_name=_("inspection"),
    )
    manufacturing_date = models.DateField(
        verbose_name=_("manufacturing date"),
    )
    expiration_date = models.DateField(
        verbose_name=_("expiration date"),
    )
    description = models.TextField(
        verbose_name=_("description"),
    )

    class Meta:
        verbose_name = _("supply lot")
        verbose_name_plural = _("supply lots")
        ordering = ["-manufacturing_date"]

    def clean(self):
        validate_manufacturing_before_expiration(
            self.manufacturing_date, self.expiration_date
        )

    def __str__(self):
        return f"Lot {self.pk} — {self.get_status_display()} (exp. {self.expiration_date})"
