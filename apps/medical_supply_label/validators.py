from django.utils.translation import gettext_lazy as _

from apps.medical_supply_label.choices import (
    MEDICAL_SUPPLY_TYPES,
    MEDICAL_SUPPLY_CATEGORIES,
)

VALID_SUPPLY_TYPES = [choice[0] for choice in MEDICAL_SUPPLY_TYPES]
VALID_CATEGORIES = [choice[0] for choice in MEDICAL_SUPPLY_CATEGORIES]


def validate_not_blank(value):
    if not value.strip():
        raise ValueError(_("This field cannot be blank."))


def validate_supply_type(value):
    if value not in VALID_SUPPLY_TYPES:
        raise ValueError(_("Invalid supply type."))


def validate_category(value):
    if value not in VALID_CATEGORIES:
        raise ValueError(_("Invalid category."))
