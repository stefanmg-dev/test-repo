import copy

import pytest

from collection_validator import validate_collections
from config_store import load_config
from document_config_resolver import (
    resolve_document_collections,
)


def schemas():
    config = load_config()

    return resolve_document_collections(
        document_config=config["invoice"],
        profile_name="electricity_electrohold",
    )


def valid_collections():
    return {
        "services": [],
        "metering_points": [
            {
                "metering_point_number": (
                    "32Z1030003158785"
                ),
            }
        ],
        "meters": [
            {
                "meter_number": "1021015029",
            }
        ],
        "consumption_items": [
            {
                "tariff": "Дневна",
                "previous_reading": "19 719",
                "current_reading": "19 929",
                "difference": "210",
                "correction": "0",
                "quantity": "210",
                "unit": "kWh",
            }
        ],
    }


def validate(collections):
    return validate_collections(
        collections=collections,
        collection_schemas=schemas(),
    )


def test_valid_electrohold_collections_pass():
    assert validate(valid_collections()) == {
        "valid": True,
        "errors": {},
    }


@pytest.mark.parametrize(
    (
        "collection_name",
        "field_name",
        "expected_message",
    ),
    [
        (
            "metering_points",
            "metering_point_number",
            "Metering point number is required",
        ),
        (
            "meters",
            "meter_number",
            "Meter number is required",
        ),
        (
            "consumption_items",
            "tariff",
            "Tariff is required",
        ),
        (
            "consumption_items",
            "quantity",
            "Consumption quantity is required",
        ),
    ],
)
def test_required_electrical_collection_fields(
    collection_name,
    field_name,
    expected_message,
):
    collections = copy.deepcopy(
        valid_collections()
    )
    collections[collection_name][0][field_name] = None

    result = validate(collections)

    assert result["valid"] is False
    assert result["errors"][
        f"{collection_name}[0].{field_name}"
    ] == [
        expected_message,
    ]


@pytest.mark.parametrize(
    (
        "collection_name",
        "field_name",
        "invalid_value",
        "expected_message",
    ),
    [
        (
            "metering_points",
            "metering_point_number",
            "INVALID",
            "Metering point number is invalid",
        ),
        (
            "meters",
            "meter_number",
            "ABC",
            "Meter number is invalid",
        ),
        (
            "consumption_items",
            "tariff",
            "Пикова",
            "Tariff is invalid",
        ),
        (
            "consumption_items",
            "quantity",
            "-1",
            (
                "Consumption quantity must be "
                "a non-negative decimal"
            ),
        ),
    ],
)
def test_invalid_electrical_collection_values(
    collection_name,
    field_name,
    invalid_value,
    expected_message,
):
    collections = copy.deepcopy(
        valid_collections()
    )
    collections[collection_name][0][
        field_name
    ] = invalid_value

    result = validate(collections)

    assert result["valid"] is False

    error_path = (
        f"{collection_name}[0].{field_name}"
    )

    assert expected_message in result["errors"][
        error_path
    ]
