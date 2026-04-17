from django.db import models
from apps.core.models import TimeStampedModel
from django.utils.translation import gettext_lazy as _
from apps.core.validators import validate_cnpj, validate_phone_number


class Organization(TimeStampedModel):
    name = models.CharField(
        max_length=200,
        verbose_name=_("name"),
    )
    cnpj = models.CharField(
        max_length=18,
        unique=True,
        verbose_name=_("CNPJ"),
        validators=[validate_cnpj],
        help_text=_("Format: XX.XXX.XXX/XXXX-XX"),
    )
    address = models.CharField(
        max_length=255,
        verbose_name=_("address"),
    )
    phone_number = models.CharField(
        max_length=15,
        verbose_name=_("phone number"),
        validators=[validate_phone_number],
        help_text=_("Format: (XX) XXXXX-XXXX"),
    )

    class Meta:
        verbose_name = _("organization")
        verbose_name_plural = _("organizations")
        ordering = ["name"]

    def __str__(self):
        return self.name
