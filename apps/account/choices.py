from django.utils.translation import gettext_lazy as _

ACCOUNT_TYPES = [
    ("admin", _("Administrator")),
    ("manager", _("Manager")),
    ("technician", _("Technician")),
    ("auditor", _("Auditor")),
    ("operator", _("Operator")),
]
