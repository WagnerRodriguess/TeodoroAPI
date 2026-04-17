import re
from apps.account.choices import ACCOUNT_TYPES
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

VALID_ACCOUNT_TYPES = [choice[0] for choice in ACCOUNT_TYPES]

def validate_account_type(value):
    if value not in VALID_ACCOUNT_TYPES:
        raise ValidationError(_("Invalid account type."))


def validate_cpf(value):
    cpf = re.sub(r"\D", "", value)

    if len(cpf) != 11:
        raise ValidationError(_("CPF must have 11 digits."))

    if cpf == cpf[0] * 11:
        raise ValidationError(_("Invalid CPF."))

    for i, digit in enumerate([9, 10]):
        total = sum(int(cpf[j]) * ((digit + 1) - j) for j in range(digit))
        remainder = (total * 10) % 11
        if remainder == 10:
            remainder = 0
        if remainder != int(cpf[digit]):
            raise ValidationError(_("Invalid CPF."))
