from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from apps.supply.models import Supply, SupplyLabel
from apps.supply.choices import SupplyStatus
from apps.supply.validators import validate_unit_of_measure, validate_supply_status
from apps.supply_label.choices import SupplyLabelType
from apps.supply_label.validators import validate_supply_type
from apps.supply.services import SupplyLabelServices, SupplyServices
from apps.account.models import Account
from apps.account.choices import AccountType
from django.core.exceptions import ValidationError


# ── Helpers ───────────────────────────────────────────────────────────────────

def make_user(username, account_type=AccountType.ADMIN, cpf="529.982.247-25"):
    user = User.objects.create_user(
        username=username,
        password="StrongPass!23",
        email=f"{username}@test.com",
        first_name="Test",
        last_name="User",
    )
    Account.objects.create(
        user=user,
        account_type=account_type,
        cpf=cpf,
        address="Rua das Flores, 10",
        phone_number="(79) 91234-5678",
    )
    return user


def auth_header(user):
    token = RefreshToken.for_user(user).access_token
    return {"HTTP_AUTHORIZATION": f"Bearer {token}"}


def make_label(**kwargs):
    defaults = {
        "name": "Amoxicilina",
        "supply_label_type": SupplyLabelType.MEDICATION,
        "category": "Antibiótico",
        "details": "Uso veterinário",
    }
    defaults.update(kwargs)
    return SupplyLabel.objects.create(**defaults)


def make_supply(label=None, **kwargs):
    if label is None:
        label = make_label()
    defaults = {
        "supply_label": label,
        "status": SupplyStatus.ACTIVE,
        "description": "Estoque principal",
        "quantity": 100.0,
        "unit_of_measure": "mg",
    }
    defaults.update(kwargs)
    return Supply.objects.create(**defaults)


# ── Validator tests ───────────────────────────────────────────────────────────

class ValidatorTests(TestCase):

    def test_validate_unit_of_measure_valid(self):
        # should not raise
        validate_unit_of_measure(0)
        validate_unit_of_measure(50.5)

    def test_validate_unit_of_measure_negative_raises(self):
        with self.assertRaises(ValidationError):
            validate_unit_of_measure(-1)

    def test_validate_supply_status_valid(self):
        for s in SupplyStatus.values:
            validate_supply_status(s)  # should not raise

    def test_validate_supply_status_invalid_raises(self):
        with self.assertRaises(ValidationError):
            validate_supply_status("invalid_status")

    def test_validate_supply_type_valid(self):
        for t in SupplyLabelType.values:
            validate_supply_type(t)  # should not raise

    def test_validate_supply_type_invalid_raises(self):
        with self.assertRaises(ValidationError):
            validate_supply_type("invalid_type")


# ── Model tests ───────────────────────────────────────────────────────────────

class SupplyLabelModelTests(TestCase):

    def test_create_supply_label(self):
        label = make_label()
        self.assertEqual(label.name, "Amoxicilina")
        self.assertEqual(label.supply_label_type, SupplyLabelType.MEDICATION)
        self.assertEqual(label.category, "Antibiótico")

    def test_str_representation(self):
        label = make_label(name="Dipirona", supply_label_type=SupplyLabelType.MEDICATION)
        self.assertIn("Dipirona", str(label))

    def test_details_defaults_to_empty_string(self):
        label = SupplyLabel.objects.create(
            name="Vacina",
            supply_label_type=SupplyLabelType.MEDICATION,
            category="Imunização",
        )
        self.assertEqual(label.details, "")


class SupplyModelTests(TestCase):

    def test_create_supply(self):
        supply = make_supply()
        self.assertEqual(supply.quantity, 100.0)
        self.assertEqual(supply.status, SupplyStatus.ACTIVE)
        self.assertEqual(supply.unit_of_measure, "mg")

    def test_str_representation(self):
        supply = make_supply()
        self.assertIn("Amoxicilina", str(supply))
        self.assertIn("100.0", str(supply))
        self.assertIn("mg", str(supply))

    def test_status_defaults_to_active(self):
        label = make_label()
        supply = Supply.objects.create(
            supply_label=label,
            quantity=10,
            unit_of_measure="un",
        )
        self.assertEqual(supply.status, SupplyStatus.ACTIVE)

    def test_description_defaults_to_empty_string(self):
        label = make_label()
        supply = Supply.objects.create(
            supply_label=label,
            quantity=10,
            unit_of_measure="un",
        )
        self.assertEqual(supply.description, "")

    def test_supply_label_protect_on_delete(self):
        """Deleting a label that has supplies should raise ProtectedError."""
        from django.db.models import ProtectedError
        supply = make_supply()
        with self.assertRaises(ProtectedError):
            supply.supply_label.delete()


# ── Service tests ─────────────────────────────────────────────────────────────

class SupplyLabelServiceTests(TestCase):

    def test_list_all_returns_all_labels(self):
        make_label(name="Label A")
        make_label(name="Label B")
        self.assertEqual(SupplyLabelServices.list_all().count(), 2)

    def test_get_existing_label(self):
        label = make_label()
        fetched = SupplyLabelServices.get(label.pk)
        self.assertEqual(fetched.pk, label.pk)

    def test_get_nonexistent_raises_404(self):
        from django.http import Http404
        with self.assertRaises(Http404):
            SupplyLabelServices.get(9999)

    def test_create_label(self):
        data = {
            "name": "Ivermectina",
            "supply_label_type": SupplyLabelType.MEDICATION,
            "category": "Antiparasitário",
            "details": "",
        }
        label = SupplyLabelServices.create(data)
        self.assertEqual(label.name, "Ivermectina")
        self.assertTrue(SupplyLabel.objects.filter(pk=label.pk).exists())

    def test_update_label(self):
        label = make_label()
        updated = SupplyLabelServices.update(label, {"name": "Dipirona Sódica"})
        self.assertEqual(updated.name, "Dipirona Sódica")

    def test_delete_label_without_supplies(self):
        label = make_label()
        pk = label.pk
        SupplyLabelServices.delete(pk)
        self.assertFalse(SupplyLabel.objects.filter(pk=pk).exists())

    def test_delete_nonexistent_label_raises_404(self):
        from django.http import Http404
        with self.assertRaises(Http404):
            SupplyLabelServices.delete(9999)


class SupplyServiceTests(TestCase):

    def setUp(self):
        self.label = make_label()

    def test_list_all_returns_all_supplies(self):
        make_supply(self.label)
        make_supply(self.label, quantity=50)
        self.assertEqual(SupplyServices.list_all().count(), 2)

    def test_get_existing_supply(self):
        supply = make_supply(self.label)
        fetched = SupplyServices.get(supply.pk)
        self.assertEqual(fetched.pk, supply.pk)

    def test_get_nonexistent_raises_404(self):
        from django.http import Http404
        with self.assertRaises(Http404):
            SupplyServices.get(9999)

    def test_create_supply(self):
        data = {
            "supply_label": self.label,
            "status": SupplyStatus.ACTIVE,
            "description": "Lote novo",
            "quantity": 200.0,
            "unit_of_measure": "ml",
        }
        supply = SupplyServices.create(data)
        self.assertEqual(supply.quantity, 200.0)
        self.assertTrue(Supply.objects.filter(pk=supply.pk).exists())

    def test_update_supply(self):
        supply = make_supply(self.label)
        updated = SupplyServices.update(supply, {"quantity": 999.0, "status": SupplyStatus.INACTIVE})
        self.assertEqual(updated.quantity, 999.0)
        self.assertEqual(updated.status, SupplyStatus.INACTIVE)

    def test_delete_supply(self):
        supply = make_supply(self.label)
        pk = supply.pk
        SupplyServices.delete(pk)
        self.assertFalse(Supply.objects.filter(pk=pk).exists())

    def test_delete_nonexistent_supply_raises_404(self):
        from django.http import Http404
        with self.assertRaises(Http404):
            SupplyServices.delete(9999)

    def test_list_all_uses_select_related(self):
        """Ensures supply_label is prefetched (no extra queries)."""
        make_supply(self.label)
        qs = SupplyServices.list_all()
        # accessing supply_label should not fire an extra query
        with self.assertNumQueries(0):
            _ = qs[0].supply_label.name


# ── Supply Label API tests ────────────────────────────────────────────────────

class SupplyLabelListAPIViewTests(APITestCase):

    def setUp(self):
        self.admin = make_user("admin_user", AccountType.ADMIN, "529.982.247-25")
        self.customer = make_user("customer_user", AccountType.CUSTOMER, "153.509.460-56")
        self.url = reverse("supply:supply_label_list")

    # GET ── list
    def test_list_unauthenticated_returns_401(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_authenticated_returns_200(self):
        make_label()
        response = self.client.get(self.url, **auth_header(self.admin))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("data", response.data)

    def test_list_returns_correct_count(self):
        make_label(name="A")
        make_label(name="B")
        response = self.client.get(self.url, **auth_header(self.admin))
        self.assertEqual(len(response.data["data"]), 2)

    def test_customer_can_list_labels(self):
        response = self.client.get(self.url, **auth_header(self.customer))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    # POST ── create
    def test_create_unauthenticated_returns_401(self):
        payload = {"name": "X", "supply_label_type": "medication", "category": "Y"}
        response = self.client.post(self.url, payload)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_customer_cannot_create_label_returns_403(self):
        payload = {"name": "X", "supply_label_type": "medication", "category": "Y"}
        response = self.client.post(self.url, payload, **auth_header(self.customer))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_create_label_returns_201(self):
        payload = {
            "name": "Ivermectina",
            "supply_label_type": "medication",
            "category": "Antiparasitário",
            "details": "",
        }
        response = self.client.post(self.url, payload, **auth_header(self.admin))
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["data"]["name"], "Ivermectina")

    def test_create_with_invalid_type_returns_400(self):
        payload = {"name": "X", "supply_label_type": "invalid", "category": "Y"}
        response = self.client.post(self.url, payload, **auth_header(self.admin))
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_missing_required_fields_returns_400(self):
        response = self.client.post(self.url, {}, **auth_header(self.admin))
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class SupplyLabelDetailAPIViewTests(APITestCase):

    def setUp(self):
        self.admin = make_user("admin_user", AccountType.ADMIN, "529.982.247-25")
        self.customer = make_user("customer_user", AccountType.CUSTOMER, "153.509.460-56")
        self.label = make_label()
        self.url = reverse("supply:supply_label_detail", kwargs={"pk": self.label.pk})
        self.not_found_url = reverse("supply:supply_label_detail", kwargs={"pk": 9999})

    # GET ── retrieve
    def test_retrieve_unauthenticated_returns_401(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_retrieve_existing_label_returns_200(self):
        response = self.client.get(self.url, **auth_header(self.admin))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["data"]["name"], self.label.name)

    def test_retrieve_nonexistent_returns_404(self):
        response = self.client.get(self.not_found_url, **auth_header(self.admin))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_customer_can_retrieve_label(self):
        response = self.client.get(self.url, **auth_header(self.customer))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    # PATCH ── partial update
    def test_patch_unauthenticated_returns_401(self):
        response = self.client.patch(self.url, {"name": "Nova"})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_customer_cannot_patch_returns_403(self):
        response = self.client.patch(self.url, {"name": "Nova"}, **auth_header(self.customer))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_patch_label(self):
        response = self.client.patch(self.url, {"name": "Dipirona"}, **auth_header(self.admin))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["data"]["name"], "Dipirona")

    def test_patch_nonexistent_returns_404(self):
        response = self.client.patch(self.not_found_url, {"name": "X"}, **auth_header(self.admin))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    # DELETE ── destroy
    def test_delete_unauthenticated_returns_401(self):
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_customer_cannot_delete_returns_403(self):
        response = self.client.delete(self.url, **auth_header(self.customer))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_delete_label_returns_204(self):
        response = self.client.delete(self.url, **auth_header(self.admin))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(SupplyLabel.objects.filter(pk=self.label.pk).exists())

    def test_delete_nonexistent_returns_404(self):
        response = self.client.delete(self.not_found_url, **auth_header(self.admin))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


# ── Supply API tests ──────────────────────────────────────────────────────────

class SupplyListAPIViewTests(APITestCase):

    def setUp(self):
        self.admin = make_user("admin_user", AccountType.ADMIN, "529.982.247-25")
        self.customer = make_user("customer_user", AccountType.CUSTOMER, "153.509.460-56")
        self.label = make_label()
        self.url = reverse("supply:supply_list")

    def _valid_payload(self):
        return {
            "supply_label": self.label.pk,
            "status": "active",
            "description": "Estoque A",
            "quantity": 50.0,
            "unit_of_measure": "mg",
        }

    # GET ── list
    def test_list_unauthenticated_returns_401(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_authenticated_returns_200(self):
        response = self.client.get(self.url, **auth_header(self.admin))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("data", response.data)

    def test_list_returns_correct_count(self):
        make_supply(self.label)
        make_supply(self.label, quantity=20)
        response = self.client.get(self.url, **auth_header(self.admin))
        self.assertEqual(len(response.data["data"]), 2)

    def test_customer_can_list_supplies(self):
        response = self.client.get(self.url, **auth_header(self.customer))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_list_includes_supply_label_detail(self):
        make_supply(self.label)
        response = self.client.get(self.url, **auth_header(self.admin))
        item = response.data["data"][0]
        self.assertIn("supply_label_detail", item)
        self.assertEqual(item["supply_label_detail"]["name"], self.label.name)

    # POST ── create
    def test_create_unauthenticated_returns_401(self):
        response = self.client.post(self.url, self._valid_payload())
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_customer_cannot_create_supply_returns_403(self):
        response = self.client.post(self.url, self._valid_payload(), **auth_header(self.customer))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_create_supply_returns_201(self):
        response = self.client.post(self.url, self._valid_payload(), **auth_header(self.admin))
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["data"]["quantity"], 50.0)

    def test_create_with_negative_quantity_returns_400(self):
        payload = self._valid_payload()
        payload["quantity"] = -10
        response = self.client.post(self.url, payload, **auth_header(self.admin))
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_with_invalid_status_returns_400(self):
        payload = self._valid_payload()
        payload["status"] = "invalid"
        response = self.client.post(self.url, payload, **auth_header(self.admin))
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_with_nonexistent_label_returns_400(self):
        payload = self._valid_payload()
        payload["supply_label"] = 9999
        response = self.client.post(self.url, payload, **auth_header(self.admin))
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_missing_required_fields_returns_400(self):
        response = self.client.post(self.url, {}, **auth_header(self.admin))
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class SupplyDetailAPIViewTests(APITestCase):

    def setUp(self):
        self.admin = make_user("admin_user", AccountType.ADMIN, "529.982.247-25")
        self.customer = make_user("customer_user", AccountType.CUSTOMER, "153.509.460-56")
        self.label = make_label()
        self.supply = make_supply(self.label)
        self.url = reverse("supply:supply_detail", kwargs={"pk": self.supply.pk})
        self.not_found_url = reverse("supply:supply_detail", kwargs={"pk": 9999})

    # GET ── retrieve
    def test_retrieve_unauthenticated_returns_401(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_retrieve_existing_supply_returns_200(self):
        response = self.client.get(self.url, **auth_header(self.admin))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["data"]["quantity"], self.supply.quantity)

    def test_retrieve_nonexistent_returns_404(self):
        response = self.client.get(self.not_found_url, **auth_header(self.admin))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_customer_can_retrieve_supply(self):
        response = self.client.get(self.url, **auth_header(self.customer))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_retrieve_response_has_supply_label_detail(self):
        response = self.client.get(self.url, **auth_header(self.admin))
        self.assertIn("supply_label_detail", response.data["data"])

    # PATCH ── partial update
    def test_patch_unauthenticated_returns_401(self):
        response = self.client.patch(self.url, {"quantity": 999})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_customer_cannot_patch_returns_403(self):
        response = self.client.patch(self.url, {"quantity": 999}, **auth_header(self.customer))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_patch_supply(self):
        response = self.client.patch(self.url, {"quantity": 999.0}, **auth_header(self.admin))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["data"]["quantity"], 999.0)

    def test_patch_status(self):
        response = self.client.patch(self.url, {"status": "expired"}, **auth_header(self.admin))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["data"]["status"], "expired")

    def test_patch_nonexistent_returns_404(self):
        response = self.client.patch(self.not_found_url, {"quantity": 1}, **auth_header(self.admin))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_patch_with_negative_quantity_returns_400(self):
        response = self.client.patch(self.url, {"quantity": -5}, **auth_header(self.admin))
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # DELETE ── destroy
    def test_delete_unauthenticated_returns_401(self):
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_customer_cannot_delete_returns_403(self):
        response = self.client.delete(self.url, **auth_header(self.customer))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_delete_supply_returns_204(self):
        response = self.client.delete(self.url, **auth_header(self.admin))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Supply.objects.filter(pk=self.supply.pk).exists())

    def test_delete_nonexistent_returns_404(self):
        response = self.client.delete(self.not_found_url, **auth_header(self.admin))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)