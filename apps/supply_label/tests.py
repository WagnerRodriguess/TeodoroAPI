from django.test import TestCase
from django.http import Http404
from rest_framework.test import APIClient
from apps.supply_label.models import SupplyLabel
from apps.supply_label.serializers import SupplyLabelSerializer
from apps.supply_label.services import SupplyLabelServices
from apps.supply_label.validators import validate_supply_type, validate_category
from apps.supply_label.choices import SupplyLabelType, SupplyLabelCategory


class SupplyLabelValidatorTests(TestCase):
    """
    Tests for ``validate_supply_type`` and ``validate_category`` — the
    standalone validator functions used by the model and the serializer.

    Valid values must pass silently; any value outside the declared
    choices must raise ``ValueError`` with an appropriate message.
    """

    # validate_supply_type

    def test_valid_supply_type_passes(self):
        """Every declared supply type must be accepted without raising."""
        for supply_type in SupplyLabelType.values:
            with self.subTest(supply_type=supply_type):
                try:
                    validate_supply_type(supply_type)
                except ValueError:
                    self.fail(
                        f"validate_supply_type raised ValueError for valid type '{supply_type}'"
                    )

    def test_invalid_supply_type_raises_value_error(self):
        """An unrecognised supply type must raise ``ValueError``."""
        with self.assertRaises(ValueError):
            validate_supply_type("unknown_type")

    def test_empty_supply_type_raises_value_error(self):
        """An empty string is not a valid supply type and must be rejected."""
        with self.assertRaises(ValueError):
            validate_supply_type("")

    # validate_category

    def test_valid_category_passes(self):
        """Every declared category must be accepted without raising."""
        for category in SupplyLabelCategory.values:
            with self.subTest(category=category):
                try:
                    validate_category(category)
                except ValueError:
                    self.fail(
                        f"validate_category raised ValueError for valid category '{category}'"
                    )

    def test_invalid_category_raises_value_error(self):
        """An unrecognised category must raise ``ValueError``."""
        with self.assertRaises(ValueError):
            validate_category("unknown_category")

    def test_empty_category_raises_value_error(self):
        """An empty string is not a valid category and must be rejected."""
        with self.assertRaises(ValueError):
            validate_category("")


class SupplyLabelSerializerTests(TestCase):
    """
    Tests for ``SupplyLabelSerializer``.

    The serializer is responsible for validating supply_label_type and
    category choices (delegating to the validators), enforcing required
    fields, and exposing the expected set of fields in its output
    representation.
    """

    def _valid_payload(self, **overrides):
        payload = {
            "name": "Luva Cirúrgica",
            "supply_label_type": "equipment",
            "category": "disposable",
            "details": "Luva estéril para procedimentos cirúrgicos.",
        }
        payload.update(overrides)
        return payload

    def test_valid_payload_is_valid(self):
        """A fully-populated, well-formed payload must pass validation."""
        serializer = SupplyLabelSerializer(data=self._valid_payload())
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_details_is_optional(self):
        """``details`` is an optional field; omitting it must still pass validation."""
        serializer = SupplyLabelSerializer(data=self._valid_payload(details=None))
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_missing_name_is_invalid(self):
        """``name`` is required; its absence must produce a validation error."""
        payload = self._valid_payload(name=None)
        serializer = SupplyLabelSerializer(data=payload)
        self.assertFalse(serializer.is_valid())
        self.assertIn("name", serializer.errors)

    def test_missing_supply_label_type_is_invalid(self):
        """``supply_label_type`` is required; its absence must produce a validation error."""
        payload = self._valid_payload(supply_label_type=None)
        serializer = SupplyLabelSerializer(data=payload)
        self.assertFalse(serializer.is_valid())
        self.assertIn("supply_label_type", serializer.errors)

    def test_missing_category_is_invalid(self):
        """``category`` is required; its absence must produce a validation error."""
        payload = self._valid_payload(category=None)
        serializer = SupplyLabelSerializer(data=payload)
        self.assertFalse(serializer.is_valid())
        self.assertIn("category", serializer.errors)

    def test_invalid_supply_label_type_is_invalid(self):
        """An unrecognised ``supply_label_type`` value must be rejected."""
        serializer = SupplyLabelSerializer(
            data=self._valid_payload(supply_label_type="radioactive")
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn("supply_label_type", serializer.errors)

    def test_invalid_category_is_invalid(self):
        """An unrecognised ``category`` value must be rejected."""
        serializer = SupplyLabelSerializer(
            data=self._valid_payload(category="unknown_cat")
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn("category", serializer.errors)

    def test_representation_contains_expected_fields(self):
        """
        Serialized output must expose exactly the contracted fields:
        ``id``, ``name``, ``supply_label_type``, ``category`` and
        ``details`` — nothing more, nothing less.
        """
        supply_label = SupplyLabel.objects.create(
            name="Soro Fisiológico",
            supply_label_type="medication",
            category="therapeutic",
            details="500 ml.",
        )
        data = SupplyLabelSerializer(supply_label).data
        self.assertIn("id", data)
        self.assertEqual(data["name"], "Soro Fisiológico")
        self.assertEqual(data["supply_label_type"], "medication")
        self.assertEqual(data["category"], "therapeutic")
        self.assertEqual(data["details"], "500 ml.")
        self.assertNotIn("created_at", data)
        self.assertNotIn("updated_at", data)

    def test_id_is_read_only(self):
        """
        ``id`` must be read-only: supplying it in the input payload must
        not cause a validation error, but it must also not be accepted as
        a writable field.
        """
        serializer = SupplyLabelSerializer(data=self._valid_payload(id=999))
        self.assertTrue(serializer.is_valid(), serializer.errors)
        self.assertNotIn("id", serializer.validated_data)


class SupplyLabelServicesTests(TestCase):
    """
    Tests for ``SupplyLabelServices`` — the service layer that wraps
    ``SupplyLabel`` persistence.

    These tests bypass HTTP and DRF and call the service methods directly
    so that failures point squarely at the service layer rather than at
    routing or serialization.
    """

    def _valid_data(self, **overrides):
        data = {
            "name": "Cateter Venoso",
            "supply_label_type": "equipment",
            "category": "disposable",
            "details": "Cateter para acesso venoso periférico.",
        }
        data.update(overrides)
        return data

    def test_create_persists_supply_label(self):
        """``create`` must persist exactly one ``SupplyLabel`` row in the database."""
        supply_label = SupplyLabelServices.create(self._valid_data())
        self.assertEqual(SupplyLabel.objects.count(), 1)
        self.assertEqual(supply_label.name, "Cateter Venoso")
        self.assertEqual(supply_label.supply_label_type, "equipment")
        self.assertEqual(supply_label.category, "disposable")

    def test_get_returns_correct_instance(self):
        """``get`` must return the exact ``SupplyLabel`` that matches the given pk."""
        created = SupplyLabel.objects.create(**self._valid_data())
        fetched = SupplyLabelServices.get(created.pk)
        self.assertEqual(fetched.pk, created.pk)

    def test_get_raises_404_for_missing_pk(self):
        """``get`` must raise ``Http404`` when no row matches the given pk."""
        with self.assertRaises(Http404):
            SupplyLabelServices.get(9999)

    def test_list_all_returns_all_instances(self):
        """``list_all`` must return every persisted ``SupplyLabel``."""
        SupplyLabel.objects.create(**self._valid_data())
        SupplyLabel.objects.create(
            **self._valid_data(name="Agulha Hipodérmica", category="reusable")
        )
        self.assertEqual(SupplyLabelServices.list_all().count(), 2)

    def test_list_all_returns_empty_queryset_when_no_records(self):
        """``list_all`` must return an empty queryset when the table is empty."""
        self.assertEqual(SupplyLabelServices.list_all().count(), 0)

    def test_update_modifies_fields(self):
        """
        ``update`` must apply every key in ``validated_data`` to the
        instance and persist the changes to the database.
        """
        supply_label = SupplyLabel.objects.create(**self._valid_data())
        updated = SupplyLabelServices.update(
            instance=supply_label,
            validated_data={"name": "Cateter Atualizado", "category": "reusable"},
        )
        supply_label.refresh_from_db()
        self.assertEqual(updated.name, "Cateter Atualizado")
        self.assertEqual(updated.category, "reusable")
        self.assertEqual(supply_label.name, "Cateter Atualizado")

    def test_delete_removes_instance(self):
        """``delete`` must hard-delete the row so no orphan record remains."""
        supply_label = SupplyLabel.objects.create(**self._valid_data())
        pk = supply_label.pk
        SupplyLabelServices.delete(pk)
        self.assertFalse(SupplyLabel.objects.filter(pk=pk).exists())

    def test_delete_raises_404_for_missing_pk(self):
        """``delete`` must raise ``Http404`` when the target row does not exist."""
        from django.http import Http404

        with self.assertRaises(Http404):
            SupplyLabelServices.delete(9999)


class SupplyLabelListAPITests(TestCase):
    """
    HTTP-level tests for ``GET /api/supply-labels/`` and
    ``POST /api/supply-labels/``.

    Covers the response envelope shape (``response.data["data"]``),
    status codes for both success and validation-error paths, and the
    persistence side-effect of a successful POST.
    """

    def setUp(self):
        self.client = APIClient()
        self.url = "/api/supply-labels/"

    def _valid_payload(self, **overrides):
        payload = {
            "name": "Máscara Cirúrgica",
            "supply_label_type": "equipment",
            "category": "disposable",
            "details": "Máscara tripla camada.",
        }
        payload.update(overrides)
        return payload

    def _create_supply_label(self, **overrides):
        return SupplyLabel.objects.create(**self._valid_payload(**overrides))

    # GET /api/supply-labels/

    def test_list_returns_200_and_data_envelope(self):
        """GET must return 200 with results nested under the ``data`` key."""
        self._create_supply_label()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertIn("data", response.data)

    def test_list_returns_all_supply_labels(self):
        """GET must return every persisted ``SupplyLabel`` in the ``data`` list."""
        self._create_supply_label(name="Item A")
        self._create_supply_label(name="Item B")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["data"]), 2)

    def test_list_returns_empty_list_when_no_records(self):
        """GET on an empty table must return 200 with an empty ``data`` list."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["data"], [])

    # POST /api/supply-labels/

    def test_post_creates_supply_label_and_returns_201(self):
        """
        A valid POST must return 201, persist one row and echo the created
        resource under the ``data`` key.
        """
        response = self.client.post(self.url, self._valid_payload(), format="json")
        self.assertEqual(response.status_code, 201, response.data)
        self.assertEqual(SupplyLabel.objects.count(), 1)
        self.assertIn("data", response.data)
        self.assertEqual(response.data["data"]["name"], "Máscara Cirúrgica")

    def test_post_response_contains_id(self):
        """The created resource in the response must include the generated ``id``."""
        response = self.client.post(self.url, self._valid_payload(), format="json")
        self.assertEqual(response.status_code, 201)
        self.assertIn("id", response.data["data"])

    def test_post_with_missing_name_returns_400(self):
        """A payload without ``name`` must return 400 with per-field errors."""
        payload = self._valid_payload(name=None)
        response = self.client.post(self.url, payload, format="json")
        self.assertEqual(response.status_code, 400)
        self.assertIn("name", response.data)

    def test_post_with_invalid_supply_label_type_returns_400(self):
        """An unrecognised ``supply_label_type`` must return 400."""
        response = self.client.post(
            self.url,
            self._valid_payload(supply_label_type="radioactive"),
            format="json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("supply_label_type", response.data)

    def test_post_with_invalid_category_returns_400(self):
        """An unrecognised ``category`` must return 400."""
        response = self.client.post(
            self.url,
            self._valid_payload(category="invalid_cat"),
            format="json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("category", response.data)

    def test_post_without_details_returns_201(self):
        """``details`` is optional; omitting it must still produce a 201."""
        response = self.client.post(self.url, self._valid_payload(details=None), format="json")
        self.assertEqual(response.status_code, 201, response.data)
        self.assertEqual(SupplyLabel.objects.count(), 1)


class SupplyLabelDetailAPITests(TestCase):
    """
    HTTP-level tests for ``/api/supply-labels/<pk>/``
    (retrieve / partial-update / delete).

    Covers the response envelope shape, 404 handling for unknown primary
    keys, partial-update semantics (only supplied fields are changed) and
    the hard-delete contract (204 with no remaining row).
    """

    def setUp(self):
        self.client = APIClient()
        self.supply_label = SupplyLabel.objects.create(
            name="Seringa Descartável",
            supply_label_type="equipment",
            category="disposable",
            details="Seringa de 10 ml.",
        )
        self.url = f"/api/supply-labels/{self.supply_label.pk}/"

    # ------------------------------------------------------------------ #
    # GET /api/supply-labels/<pk>/                                         #
    # ------------------------------------------------------------------ #

    def test_retrieve_returns_200_and_data_envelope(self):
        """GET on an existing pk must return 200 with the resource under ``data``."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertIn("data", response.data)

    def test_retrieve_returns_correct_fields(self):
        """
        The retrieved payload must expose ``id``, ``name``,
        ``supply_label_type``, ``category`` and ``details`` at the top
        level of the ``data`` object.
        """
        response = self.client.get(self.url)
        data = response.data["data"]
        self.assertEqual(data["id"], self.supply_label.pk)
        self.assertEqual(data["name"], "Seringa Descartável")
        self.assertEqual(data["supply_label_type"], "equipment")
        self.assertEqual(data["category"], "disposable")
        self.assertEqual(data["details"], "Seringa de 10 ml.")

    def test_retrieve_not_found_returns_404(self):
        """An unknown pk must return 404, not 500 or an empty body."""
        response = self.client.get("/api/supply-labels/9999/")
        self.assertEqual(response.status_code, 404)

    # PATCH /api/supply-labels/<pk>/

    def test_patch_updates_supplied_fields(self):
        """
        PATCH must update only the fields present in the payload and
        persist the changes so that a subsequent fetch reflects them.
        """
        response = self.client.patch(
            self.url,
            {"name": "Seringa Atualizada", "category": "reusable"},
            format="json",
        )
        self.assertEqual(response.status_code, 200, response.data)
        self.supply_label.refresh_from_db()
        self.assertEqual(self.supply_label.name, "Seringa Atualizada")
        self.assertEqual(self.supply_label.category, "reusable")

    def test_patch_does_not_alter_omitted_fields(self):
        """
        Fields absent from a PATCH payload must remain unchanged after
        the update — partial semantics must be enforced.
        """
        original_type = self.supply_label.supply_label_type
        self.client.patch(self.url, {"name": "Novo Nome"}, format="json")
        self.supply_label.refresh_from_db()
        self.assertEqual(self.supply_label.supply_label_type, original_type)

    def test_patch_response_contains_updated_data(self):
        """The PATCH response must echo the full updated resource under ``data``."""
        response = self.client.patch(
            self.url, {"name": "Nome Modificado"}, format="json"
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("data", response.data)
        self.assertEqual(response.data["data"]["name"], "Nome Modificado")

    def test_patch_with_invalid_supply_label_type_returns_400(self):
        """A PATCH with an unrecognised ``supply_label_type`` must return 400."""
        response = self.client.patch(
            self.url, {"supply_label_type": "radioactive"}, format="json"
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("supply_label_type", response.data)

    def test_patch_with_invalid_category_returns_400(self):
        """A PATCH with an unrecognised ``category`` must return 400."""
        response = self.client.patch(
            self.url, {"category": "unknown_cat"}, format="json"
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("category", response.data)

    def test_patch_not_found_returns_404(self):
        """PATCH on an unknown pk must return 404."""
        response = self.client.patch(
            "/api/supply-labels/9999/", {"name": "X"}, format="json"
        )
        self.assertEqual(response.status_code, 404)

    # DELETE /api/supply-labels/<pk>/

    def test_delete_returns_204_and_removes_row(self):
        """
        DELETE must return 204 and remove the row so that no orphan
        record remains in the database.
        """
        pk = self.supply_label.pk
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, 204)
        self.assertFalse(SupplyLabel.objects.filter(pk=pk).exists())

    def test_delete_not_found_returns_404(self):
        """DELETE on an unknown pk must return 404."""
        response = self.client.delete("/api/supply-labels/9999/")
        self.assertEqual(response.status_code, 404)