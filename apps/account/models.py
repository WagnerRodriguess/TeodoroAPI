from django.db import models
from django.contrib.auth.models import User
from apps.core.models import TimeStampedModel
from apps.account.choices import ACCOUNT_TYPES
from apps.organization.models import Organization
from django.utils.translation import gettext_lazy as _
from apps.core.validators import validate_phone_number
from apps.account.validators import validate_account_type, validate_cpf


class Account(TimeStampedModel):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="account",
        verbose_name=_("user"),
    )
    account_type = models.CharField(
        max_length=20,
        choices=ACCOUNT_TYPES,
        verbose_name=_("account type"),
        validators=[validate_account_type],
    )
    organization = models.OneToOneField(
        Organization,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="account",
        verbose_name=_("organization"),
    )
    cpf = models.CharField(
        max_length=14,
        unique=True,
        verbose_name=_("CPF"),
        validators=[validate_cpf],
        help_text=_("Format: XXX.XXX.XXX-XX"),
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
        verbose_name = _("account")
        verbose_name_plural = _("accounts")
        ordering = ["user__username"]

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} ({self.get_account_type_display()})"
