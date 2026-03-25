from django.utils.translation import gettext_lazy as _

MEDICAL_SUPPLY_TYPES = [
    ("medication", _("Medication")),
    ("equipment", _("Equipment")),
    ("sterilization", _("Sterilization")),
    ("nutrition", _("Nutrition")),
    ("blood_product", _("Blood Product")),
    ("other", _("Other")),
]

MEDICAL_SUPPLY_CATEGORIES = [
    ("disposable", _("Disposable")),
    ("reusable", _("Reusable")),
    ("implantable", _("Implantable")),
    ("diagnostic", _("Diagnostic")),
    ("therapeutic", _("Therapeutic")),
    ("other", _("Other")),
]
