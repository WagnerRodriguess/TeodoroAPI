from django.db import models
from django.contrib.auth.models import User
from apps.core.models import TimeStampedModel
from django.utils.translation import gettext_lazy as _
from apps.inspection.validators import validate_responsible_is_auditor


class Inspection(TimeStampedModel):
    is_complete = models.BooleanField(
        default=False,
        verbose_name=_("is complete"),
    )
    date = models.DateField(
        verbose_name=_("date"),
    )
    completion_date = models.DateField(
        null=True,
        blank=True,
        verbose_name=_("completion date"),
    )
    responsible = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name="inspections",
        verbose_name=_("responsible"),
        validators=[validate_responsible_is_auditor],
    )

    class Meta:
        verbose_name = _("inspection")
        verbose_name_plural = _("inspections")
        ordering = ["-date"]

    def __str__(self):
        status = _("complete") if self.is_complete else _("pending")
        return f"Inspection {self.pk} — {self.date} ({status})"
