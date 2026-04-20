from django.contrib.auth.models import User
from django.core.exceptions import ValidationError as DjangoValidationError
from django.test import TestCase
from rest_framework.test import APIClient

from apps.account.models import Account
from apps.organization.models import Organization
from apps.organization.serializers import OrganizationSerializer
from apps.organization.services import OrganizationServices


class OrganizationSerializerTests(TestCase):
    """
    Tests for ``OrganizationSerializer``.

    The serializer exposes a flat representation of ``Organization`` and
    is responsible for validating business rules such as CNPJ format
    (including check-digit), CNPJ uniqueness and phone number format.
    """

    def _valid_payload(self, **overrides):
        payload = {
            "name": "Hospital Teodoro",
            "cnpj": "11.222.333/0001-81",
            "address": "Av. Paulista, 1000",
            "phone_number": "(11) 91234-5678",
        }
        payload.update(overrides)
        return payload

    def test_valid_payload_is_valid(self):
        """A fully-populated, well-formed payload must pass validation."""
        serializer = OrganizationSerializer(data=self._valid_payload())
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_missing_name_is_invalid(self):
        """``name`` is required and its absence must be reported as an error."""
        payload = self._valid_payload()
        payload.pop("name")
        serializer = OrganizationSerializer(data=payload)
        self.assertFalse(serializer.is_valid())
        self.assertIn("name", serializer.errors)

    def test_invalid_cnpj_is_invalid(self):
        """
        CNPJs with invalid check digits (e.g. ``00.000.000/0000-00``) must
        be rejected by the custom CNPJ validator.
        """
        serializer = OrganizationSerializer(
            data=self._valid_payload(cnpj="00.000.000/0000-00")
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn("cnpj", serializer.errors)

    def test_duplicate_cnpj_is_invalid(self):
        """A CNPJ already persisted on another organization must be rejected."""
        Organization.objects.create(
            name="Other",
            cnpj="11.222.333/0001-81",
            address="Rua X, 1",
            phone_number="(11) 91234-5678",
        )
        serializer = OrganizationSerializer(data=self._valid_payload())
        self.assertFalse(serializer.is_valid())
        self.assertIn("cnpj", serializer.errors)

    def test_invalid_phone_number_is_invalid(self):
        """Phone numbers without 10 or 11 digits must be rejected."""
        serializer = OrganizationSerializer(
            data=self._valid_payload(phone_number="123")
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn("phone_number", serializer.errors)

    def test_to_representation_is_flat(self):
        """Output must be a flat object exposing every persisted field."""
        organization = Organization.objects.create(
            name="Hospital Teodoro",
            cnpj="11.222.333/0001-81",
            address="Av. Paulista, 1000",
            phone_number="(11) 91234-5678",
        )
        data = OrganizationSerializer(organization).data
        self.assertEqual(data["name"], "Hospital Teodoro")
        self.assertEqual(data["cnpj"], "11.222.333/0001-81")
        self.assertEqual(data["address"], "Av. Paulista, 1000")
        self.assertEqual(data["phone_number"], "(11) 91234-5678")
        self.assertIn("id", data)
        self.assertIn("created_at", data)


class OrganizationServicesTests(TestCase):
    """
    Tests for ``OrganizationServices`` — the service layer that owns
    ``Organization`` persistence.

    These tests focus on transactional create, partial updates, hard
    delete and the list queryset. They bypass HTTP and call the services
    directly so failures point squarely at the service layer.
    """

    def _valid_data(self, **overrides):
        data = {
            "name": "Hospital Teodoro",
            "cnpj": "11.222.333/0001-81",
            "address": "Av. Paulista, 1000",
            "phone_number": "(11) 91234-5678",
        }
        data.update(overrides)
        return data

    def test_create_persists_organization(self):
        """``create`` must persist exactly one ``Organization`` row with the supplied fields."""
        organization = OrganizationServices.create(self._valid_data())
        self.assertEqual(Organization.objects.count(), 1)
        self.assertEqual(organization.name, "Hospital Teodoro")
        self.assertEqual(organization.cnpj, "11.222.333/0001-81")

    def test_create_rolls_back_on_invalid_cnpj(self):
        """
        If ``full_clean`` rejects the payload (invalid CNPJ) the atomic
        block must roll back so no partial row is persisted.
        """
        bad_data = self._valid_data(cnpj="00.000.000/0000-00")
        with self.assertRaises(DjangoValidationError):
            OrganizationServices.create(bad_data)
        self.assertEqual(Organization.objects.count(), 0)

    def test_update_changes_fields(self):
        """``update`` must apply partial updates to arbitrary subsets of fields."""
        organization = OrganizationServices.create(self._valid_data())
        updated = OrganizationServices.update(
            organization,
            {"name": "Novo Nome", "address": "Rua Nova, 42"},
        )
        updated.refresh_from_db()
        self.assertEqual(updated.name, "Novo Nome")
        self.assertEqual(updated.address, "Rua Nova, 42")
        self.assertEqual(updated.cnpj, "11.222.333/0001-81")

    def test_delete_removes_organization(self):
        """``delete`` must hard-delete the ``Organization`` row."""
        organization = OrganizationServices.create(self._valid_data())
        OrganizationServices.delete(organization.pk)
        self.assertEqual(Organization.objects.count(), 0)

    def test_list_all_returns_every_row(self):
        """``list_all`` must return every persisted ``Organization``."""
        OrganizationServices.create(self._valid_data())
        OrganizationServices.create(
            self._valid_data(name="Outra", cnpj="45.997.418/0001-53")
        )
        self.assertEqual(OrganizationServices.list_all().count(), 2)


class OrganizationCreateAPITests(TestCase):
    """
    HTTP-level tests for ``POST /api/organizations/``.

    Creation is restricted to authenticated non-customer users: anonymous
    requests receive 401, customers receive 403, and admins persist the
    organization under the ``data`` envelope.
    """

    def setUp(self):
        self.client = APIClient()
        self.url = "/api/organizations/"
        self.customer = self._make_account(
            "customeruser", "customer", "111.444.777-35"
        )
        self.admin = self._make_account("adminuser", "admin", "529.982.247-25")

    def _make_account(self, username, account_type, cpf):
        user = User.objects.create_user(
            username=username, password="Pw12345!", email=f"{username}@example.com"
        )
        return Account.objects.create(
            user=user,
            account_type=account_type,
            cpf=cpf,
            address="Rua X, 1",
            phone_number="(11) 91234-5678",
        )

    def _valid_payload(self, **overrides):
        payload = {
            "name": "Hospital Teodoro",
            "cnpj": "11.222.333/0001-81",
            "address": "Av. Paulista, 1000",
            "phone_number": "(11) 91234-5678",
        }
        payload.update(overrides)
        return payload

    def test_create_requires_authentication(self):
        """Anonymous requests must get 401, not 403 or 201."""
        response = self.client.post(self.url, self._valid_payload(), format="json")
        self.assertEqual(response.status_code, 401)
        self.assertEqual(Organization.objects.count(), 0)

    def test_create_forbidden_for_customer(self):
        """Authenticated customers cannot create organizations (403)."""
        self.client.force_authenticate(self.customer.user)
        response = self.client.post(self.url, self._valid_payload(), format="json")
        self.assertEqual(response.status_code, 403)
        self.assertEqual(Organization.objects.count(), 0)

    def test_create_allowed_for_admin(self):
        """
        Admins can create organizations: the endpoint returns 201, persists
        the row and echoes the created resource under ``data``.
        """
        self.client.force_authenticate(self.admin.user)
        response = self.client.post(self.url, self._valid_payload(), format="json")
        self.assertEqual(response.status_code, 201, response.data)
        self.assertEqual(Organization.objects.count(), 1)
        self.assertEqual(response.data["data"]["name"], "Hospital Teodoro")
        self.assertEqual(response.data["data"]["cnpj"], "11.222.333/0001-81")

    def test_create_with_invalid_cnpj_returns_400(self):
        """Invalid payloads surface as 400 with per-field errors (here ``cnpj``)."""
        self.client.force_authenticate(self.admin.user)
        response = self.client.post(
            self.url,
            self._valid_payload(cnpj="00.000.000/0000-00"),
            format="json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("cnpj", response.data)


class OrganizationListAPITests(TestCase):
    """
    HTTP-level tests for ``GET /api/organizations/``.

    Listing is open to every client (authentication is not required). The
    response must always be wrapped in the ``data`` envelope and include
    every persisted organization.
    """

    def setUp(self):
        self.client = APIClient()
        self.url = "/api/organizations/"
        Organization.objects.create(
            name="Hospital Teodoro",
            cnpj="11.222.333/0001-81",
            address="Av. Paulista, 1000",
            phone_number="(11) 91234-5678",
        )
        Organization.objects.create(
            name="Outra Clinica",
            cnpj="45.997.418/0001-53",
            address="Rua Y, 2",
            phone_number="(11) 91234-5678",
        )

    def test_list_allowed_for_anonymous(self):
        """Anonymous clients can list every organization under the ``data`` key."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["data"]), 2)


class OrganizationDetailAPITests(TestCase):
    """
    HTTP-level tests for ``/api/organizations/<pk>/`` (retrieve/update/delete).

    Covers authorization (GET open to anyone; PATCH/DELETE restricted to
    non-customer authenticated users), the flat response shape and the
    hard-delete semantics.
    """

    def setUp(self):
        self.client = APIClient()
        self.customer = self._make_account(
            "customeruser", "customer", "111.444.777-35"
        )
        self.admin = self._make_account("adminuser", "admin", "529.982.247-25")
        self.organization = Organization.objects.create(
            name="Hospital Teodoro",
            cnpj="11.222.333/0001-81",
            address="Av. Paulista, 1000",
            phone_number="(11) 91234-5678",
        )
        self.url = f"/api/organizations/{self.organization.pk}/"

    def _make_account(self, username, account_type, cpf):
        user = User.objects.create_user(
            username=username, password="Pw12345!", email=f"{username}@example.com"
        )
        return Account.objects.create(
            user=user,
            account_type=account_type,
            cpf=cpf,
            address="Rua X, 1",
            phone_number="(11) 91234-5678",
        )

    def test_retrieve_allowed_for_anonymous(self):
        """GET on a detail URL is open to anonymous clients and returns 200."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        data = response.data["data"]
        self.assertEqual(data["name"], "Hospital Teodoro")
        self.assertEqual(data["cnpj"], "11.222.333/0001-81")

    def test_retrieve_not_found(self):
        """Unknown primary keys return 404 with the ``error`` envelope."""
        response = self.client.get("/api/organizations/9999/")
        self.assertEqual(response.status_code, 404)
        self.assertIn("error", response.data)

    def test_patch_requires_authentication(self):
        """Unauthenticated PATCH requests must get 401."""
        response = self.client.patch(
            self.url, {"name": "Novo"}, format="json"
        )
        self.assertEqual(response.status_code, 401)

    def test_patch_forbidden_for_customer(self):
        """Customers cannot update organizations (403 via ``IsNotCustomer``)."""
        self.client.force_authenticate(self.customer.user)
        response = self.client.patch(
            self.url, {"name": "Novo"}, format="json"
        )
        self.assertEqual(response.status_code, 403)

    def test_patch_allowed_for_admin(self):
        """Admins can PATCH fields; response echoes updated data under ``data``."""
        self.client.force_authenticate(self.admin.user)
        response = self.client.patch(
            self.url,
            {"name": "Novo Nome", "address": "Rua Nova, 42"},
            format="json",
        )
        self.assertEqual(response.status_code, 200, response.data)
        self.organization.refresh_from_db()
        self.assertEqual(self.organization.name, "Novo Nome")
        self.assertEqual(self.organization.address, "Rua Nova, 42")
        self.assertEqual(response.data["data"]["name"], "Novo Nome")

    def test_delete_requires_authentication(self):
        """Unauthenticated DELETE requests must get 401."""
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, 401)
        self.assertTrue(Organization.objects.filter(pk=self.organization.pk).exists())

    def test_delete_forbidden_for_customer(self):
        """Customers cannot delete organizations (403)."""
        self.client.force_authenticate(self.customer.user)
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, 403)
        self.assertTrue(Organization.objects.filter(pk=self.organization.pk).exists())

    def test_delete_allowed_for_admin(self):
        """Admins can delete; the operation returns 204 and removes the row."""
        self.client.force_authenticate(self.admin.user)
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, 204)
        self.assertFalse(Organization.objects.filter(pk=self.organization.pk).exists())

    def test_delete_not_found(self):
        """Deleting an unknown pk returns 404 with the ``error`` envelope."""
        self.client.force_authenticate(self.admin.user)
        response = self.client.delete("/api/organizations/9999/")
        self.assertEqual(response.status_code, 404)
        self.assertIn("error", response.data)
