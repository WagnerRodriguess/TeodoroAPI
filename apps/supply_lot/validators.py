from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from apps.supply_lot.choices import SUPPLY_LOT_STATUSES

# Why use this notation?
VALID_STATUSES = [choice[0] for choice in SUPPLY_LOT_STATUSES]

def validate_status(value):
    if value not in VALID_STATUSES:
        raise ValidationError(_("Invalid supply lot status."))


def validate_manufacturing_before_expiration(manufacturing_date, expiration_date):
    if manufacturing_date >= expiration_date:
        raise ValidationError(
            _("Manufacturing date must be before expiration date.")
        )
