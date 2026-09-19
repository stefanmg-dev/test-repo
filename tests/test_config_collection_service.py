from copy import deepcopy

import pytest
from fastapi import HTTPException

import config_collection_service as service


DOCUMENT_COLLECTION = {
    "cardinality": "zero_or_more",
    "fields": [],
}
FIELD = {
    "name": "meter_number",
    "type": "regex",
    "rule": r"Meter\s*([0-9]+)",
}
RENAMED_FIELD = {
    **FIELD,
    "name": "serial_number",
}


def legacy_config():
    return {"invoice": {"fields": []}}


def document_config():
    return {
        "invoice": {
            "fields": [],
            "collections": {
                "meters": deepcopy(DOCUMENT_COLLECTION),
            },
        }
    }


def profile_config():
    return {
        "invoice": {
            "common_fields": [],
            "profiles": {
                "electricity_electrohold": {
                    "fields": [],
                    "collections": {
                        "meters": deepcopy(DOCUMENT_COLLECTION),
                    },
                }
            },
            "default_profile": "electricity_electrohold",
        }
    }


@pytest.fixture
def saved_configs(monkeypatch):
    saved = []

    def capture(config):
        saved.append(deepcopy(config))

    monkeypatch.setattr(service, "save_validated_config", capture)
    return saved


def assert_http_error(call, status_code, detail):
    with pytest.raises(HTTPException) as exc_info:
        call()
    assert exc_info.value.status_code == status_code
    assert exc_info.value.detail == detail


def test_document_collection_crud_and_input_immutability(saved_configs):
    config = legacy_config()
    original = deepcopy(config)

    service.add_document_collection(
        config=config,
        document_type="invoice",
        collection_name="meters",
        collection_data=deepcopy(DOCUMENT_COLLECTION),
    )
    assert config == original
    assert saved_configs[-1]["invoice"]["collections"]["meters"] == (
        DOCUMENT_COLLECTION
    )

    config = saved_configs[-1]
    updated = {
        "cardinality": "one_or_more",
        "fields": [],
    }
    service.update_document_collection(
        config=config,
        document_type="invoice",
        collection_name="meters",
        collection_data=updated,
    )
    assert saved_configs[-1]["invoice"]["collections"]["meters"] == updated

    service.delete_document_collection(
        config=saved_configs[-1],
        document_type="invoice",
        collection_name="meters",
    )
    assert "collections" not in saved_configs[-1]["invoice"]


def test_document_collection_errors(saved_configs):
    config = document_config()
    assert_http_error(
        lambda: service.add_document_collection(
            config,
            "invoice",
            "meters",
            deepcopy(DOCUMENT_COLLECTION),
        ),
        409,
        "Collection 'meters' already exists in document type 'invoice'",
    )
    assert_http_error(
        lambda: service.update_document_collection(
            config,
            "invoice",
            "missing",
            deepcopy(DOCUMENT_COLLECTION),
        ),
        404,
        "Collection 'missing' was not found in document type 'invoice'",
    )
    assert_http_error(
        lambda: service.delete_document_collection(
            config,
            "invoice",
            "missing",
        ),
        404,
        "Collection 'missing' was not found in document type 'invoice'",
    )


def test_profile_collection_crud_and_input_immutability(saved_configs):
    config = profile_config()
    del config["invoice"]["profiles"]["electricity_electrohold"][
        "collections"
    ]
    original = deepcopy(config)

    service.add_profile_collection_mutation(
        config=config,
        document_type="invoice",
        profile_name="electricity_electrohold",
        collection_name="meters",
        collection_data=deepcopy(DOCUMENT_COLLECTION),
    )
    assert config == original
    profile = saved_configs[-1]["invoice"]["profiles"][
        "electricity_electrohold"
    ]
    assert profile["collections"]["meters"] == DOCUMENT_COLLECTION

    updated = {
        "cardinality": "one_or_more",
        "fields": [],
    }
    service.update_profile_collection_mutation(
        config=saved_configs[-1],
        document_type="invoice",
        profile_name="electricity_electrohold",
        collection_name="meters",
        collection_data=updated,
    )
    profile = saved_configs[-1]["invoice"]["profiles"][
        "electricity_electrohold"
    ]
    assert profile["collections"]["meters"] == updated

    service.delete_profile_collection_mutation(
        config=saved_configs[-1],
        document_type="invoice",
        profile_name="electricity_electrohold",
        collection_name="meters",
    )
    profile = saved_configs[-1]["invoice"]["profiles"][
        "electricity_electrohold"
    ]
    assert "collections" not in profile


def test_profile_collection_errors(saved_configs):
    config = profile_config()
    assert_http_error(
        lambda: service.add_profile_collection_mutation(
            config,
            "invoice",
            "electricity_electrohold",
            "meters",
            deepcopy(DOCUMENT_COLLECTION),
        ),
        409,
        "Collection 'meters' already exists in profile "
        "'electricity_electrohold'",
    )
    assert_http_error(
        lambda: service.update_profile_collection_mutation(
            config,
            "invoice",
            "electricity_electrohold",
            "missing",
            deepcopy(DOCUMENT_COLLECTION),
        ),
        404,
        "Collection 'missing' was not found in profile "
        "'electricity_electrohold'",
    )
    assert_http_error(
        lambda: service.resolve_profile_collection_target(
            legacy_config(),
            "invoice",
            "electricity_electrohold",
        ),
        409,
        "Document type uses legacy fields configuration",
    )


def test_document_collection_field_crud_and_input_immutability(saved_configs):
    config = document_config()
    original = deepcopy(config)

    service.add_document_collection_field(
        config=config,
        document_type="invoice",
        collection_name="meters",
        field_data=deepcopy(FIELD),
    )
    assert config == original
    fields = saved_configs[-1]["invoice"]["collections"]["meters"]["fields"]
    assert fields == [FIELD]

    service.update_document_collection_field(
        config=saved_configs[-1],
        document_type="invoice",
        collection_name="meters",
        field_name="meter_number",
        field_data=deepcopy(RENAMED_FIELD),
    )
    fields = saved_configs[-1]["invoice"]["collections"]["meters"]["fields"]
    assert fields == [RENAMED_FIELD]

    service.delete_document_collection_field(
        config=saved_configs[-1],
        document_type="invoice",
        collection_name="meters",
        field_name="serial_number",
    )
    fields = saved_configs[-1]["invoice"]["collections"]["meters"]["fields"]
    assert fields == []


def test_document_collection_field_conflicts_and_missing(saved_configs):
    config = document_config()
    config["invoice"]["collections"]["meters"]["fields"] = [
        deepcopy(FIELD),
        deepcopy(RENAMED_FIELD),
    ]
    assert_http_error(
        lambda: service.add_document_collection_field(
            config,
            "invoice",
            "meters",
            deepcopy(FIELD),
        ),
        409,
        "Field 'meter_number' already exists in collection 'meters'",
    )
    assert_http_error(
        lambda: service.update_document_collection_field(
            config,
            "invoice",
            "meters",
            "meter_number",
            deepcopy(RENAMED_FIELD),
        ),
        409,
        "Field 'serial_number' already exists in collection 'meters'",
    )
    assert_http_error(
        lambda: service.delete_document_collection_field(
            config,
            "invoice",
            "meters",
            "missing",
        ),
        404,
        "Field 'missing' was not found in collection 'meters'",
    )


def test_profile_collection_field_crud_and_input_immutability(saved_configs):
    config = profile_config()
    original = deepcopy(config)

    service.add_profile_collection_field(
        config=config,
        document_type="invoice",
        profile_name="electricity_electrohold",
        collection_name="meters",
        field_data=deepcopy(FIELD),
    )
    assert config == original
    fields = saved_configs[-1]["invoice"]["profiles"][
        "electricity_electrohold"
    ]["collections"]["meters"]["fields"]
    assert fields == [FIELD]

    service.update_profile_collection_field(
        config=saved_configs[-1],
        document_type="invoice",
        profile_name="electricity_electrohold",
        collection_name="meters",
        field_name="meter_number",
        field_data=deepcopy(RENAMED_FIELD),
    )
    fields = saved_configs[-1]["invoice"]["profiles"][
        "electricity_electrohold"
    ]["collections"]["meters"]["fields"]
    assert fields == [RENAMED_FIELD]

    service.delete_profile_collection_field(
        config=saved_configs[-1],
        document_type="invoice",
        profile_name="electricity_electrohold",
        collection_name="meters",
        field_name="serial_number",
    )
    fields = saved_configs[-1]["invoice"]["profiles"][
        "electricity_electrohold"
    ]["collections"]["meters"]["fields"]
    assert fields == []


def test_profile_collection_field_conflicts_and_missing(saved_configs):
    config = profile_config()
    fields = config["invoice"]["profiles"]["electricity_electrohold"][
        "collections"
    ]["meters"]["fields"]
    fields.extend([deepcopy(FIELD), deepcopy(RENAMED_FIELD)])

    assert_http_error(
        lambda: service.add_profile_collection_field(
            config,
            "invoice",
            "electricity_electrohold",
            "meters",
            deepcopy(FIELD),
        ),
        409,
        "Field 'meter_number' already exists in profile collection 'meters'",
    )
    assert_http_error(
        lambda: service.update_profile_collection_field(
            config,
            "invoice",
            "electricity_electrohold",
            "meters",
            "meter_number",
            deepcopy(RENAMED_FIELD),
        ),
        409,
        "Field 'serial_number' already exists in profile collection 'meters'",
    )
    assert_http_error(
        lambda: service.delete_profile_collection_field(
            config,
            "invoice",
            "electricity_electrohold",
            "meters",
            "missing",
        ),
        404,
        "Field 'missing' was not found in profile collection 'meters'",
    )


def test_missing_document_profile_and_collections(saved_configs):
    assert_http_error(
        lambda: service.resolve_document_collection_target({}, "invoice"),
        404,
        "Document type 'invoice' was not found",
    )
    assert_http_error(
        lambda: service.resolve_profile_collection_target(
            profile_config(),
            "invoice",
            "missing",
        ),
        404,
        "Profile 'missing' was not found",
    )
    assert_http_error(
        lambda: service.get_collection_or_404(
            document_config()["invoice"],
            "missing",
        ),
        404,
        "Collection 'missing' was not found",
    )
    profile = profile_config()["invoice"]["profiles"][
        "electricity_electrohold"
    ]
    assert_http_error(
        lambda: service.get_profile_collection_or_404(
            profile,
            "missing",
        ),
        404,
        "Collection 'missing' was not found in profile",
    )
