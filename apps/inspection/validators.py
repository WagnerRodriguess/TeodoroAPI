from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from apps.account.choices import ACCOUNT_TYPES

User = get_user_model()
AUDITOR_TYPE = next(value for value, _ in ACCOUNT_TYPES if value == "auditor")

def validate_responsible_is_auditor(user_id):
    try:
        user = User.objects.select_related("account").get(pk=user_id)
        account = user.account
    except (User.DoesNotExist, User.account.RelatedObjectDoesNotExist):
        raise ValidationError(_("Responsible user must have an account."))

    if account.account_type != AUDITOR_TYPE:
        raise ValidationError(
            _("Responsible must be a user with account type 'auditor'.")
        )
