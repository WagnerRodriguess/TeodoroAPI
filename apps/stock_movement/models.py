from django.db import models
from apps.supply.models import Supply
from apps.request.models import Request
from django.contrib.auth.models import User
from apps.supply_lot.models import SupplyLot
from apps.core.models import TimeStampedModel
from django.utils.translation import gettext_lazy as _
from apps.stock_movement.choices import StockMovementType


class StockMovement(TimeStampedModel):
    type_of_movement = models.CharField(
        max_length=20,
        choices=StockMovementType.choices,
        verbose_name=_("type of movement"),
    )
    user = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name="stock_movements",
        verbose_name=_("user"),
    )
    supply = models.ForeignKey(
        Supply,
        on_delete=models.PROTECT,
        related_name="stock_movements",
        verbose_name=_("supply"),
    )
    supply_lots = (
        models.ManyToManyField(  # Should it be in Supply or SupplyMovement?
            SupplyLot,
            related_name="stock_movements",
            verbose_name=_("supply lots"),
        )
    )
    request = models.OneToOneField(
        Request,
        on_delete=models.PROTECT,
        related_name="stock_movement",
        verbose_name=_("request"),
    )
    description = models.TextField(
        verbose_name=_("description"),
        blank=True,
        null=True,
    )

    class Meta:
        verbose_name = _("stock movement")
        verbose_name_plural = _("stock movements")
        ordering = ["-created_at"]

    def __str__(self):
        return (
            f"{self.get_type_of_movement_display()} — {self.supply} ({self.quantity})"
        )
