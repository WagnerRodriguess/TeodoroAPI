from django.utils.translation import gettext_lazy as _

SUPPLY_LOT_STATUSES = [
    ("pending", _("Pending")),
    ("approved", _("Approved")),
    ("rejected", _("Rejected")),
    ("quarantine", _("Quarantine")),
    ("expired", _("Expired")),
]
