from config_store import load_config
from document_config_resolver import (
    resolve_document_collections,
)


COLLECTION_NAMES = {
    "services",
    "metering_points",
    "meters",
    "consumption_items",
}


def resolve_collections(profile_name):
    config = load_config()

    return resolve_document_collections(
        document_config=config["invoice"],
        profile_name=profile_name,
    )


def assert_empty_collection_schema(schema):
    assert schema["cardinality"] == "zero_or_more"
    assert schema["fields"] == []
    assert schema.get("start_pattern") in {
        None,
        "",
    }


def test_a1_does_not_receive_provider_specific_collections():
    collections = resolve_collections("telecom_a1")

    assert set(collections) == COLLECTION_NAMES

    for schema in collections.values():
        assert_empty_collection_schema(schema)


def test_unknown_supplier_uses_only_empty_common_collections():
    collections = resolve_collections(None)

    assert set(collections) == COLLECTION_NAMES

    for schema in collections.values():
        assert_empty_collection_schema(schema)


def test_electrohold_receives_only_electricity_collections():
    collections = resolve_collections(
        "electricity_electrohold"
    )

    assert set(collections) == COLLECTION_NAMES

    assert_empty_collection_schema(
        collections["services"]
    )

    assert collections["metering_points"]["fields"]
    assert collections["metering_points"]["start_pattern"]

    assert collections["meters"]["fields"]
    assert collections["meters"]["start_pattern"]

    assert collections["consumption_items"]["fields"]
    assert collections["consumption_items"]["start_pattern"]


def test_toplofikacia_receives_only_heating_services():
    collections = resolve_collections(
        "heating_toplofikacia_sofia"
    )

    assert set(collections) == COLLECTION_NAMES

    assert collections["services"]["fields"]
    assert collections["services"]["start_pattern"]

    assert_empty_collection_schema(
        collections["metering_points"]
    )
    assert_empty_collection_schema(
        collections["meters"]
    )
    assert_empty_collection_schema(
        collections["consumption_items"]
    )


def test_collection_schemas_are_independent_copies():
    a1_collections = resolve_collections("telecom_a1")
    heating_collections = resolve_collections(
        "heating_toplofikacia_sofia"
    )

    heating_collections["services"]["fields"].append(
        {
            "name": "temporary_test_field",
            "type": "constant",
            "value": "temporary",
            "validation": [],
        }
    )

    refreshed_a1 = resolve_collections("telecom_a1")

    assert (
        refreshed_a1["services"]
        == a1_collections["services"]
    )
    assert refreshed_a1["services"]["fields"] == []
