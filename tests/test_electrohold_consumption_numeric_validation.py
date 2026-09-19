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
        "metering_points": [],
        "meters": [],
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


def test_valid_consumption_numeric_fields_pass():
    assert validate(valid_collections()) == {
        "valid": True,
        "errors": {},
    }


@pytest.mark.parametrize(
    (
        "field_name",
        "expected_message",
    ),
    [
        (
            "previous_reading",
            "Previous reading is required",
        ),
        (
            "current_reading",
            "Current reading is required",
        ),
        (
            "difference",
            "Consumption difference is required",
        ),
        (
            "correction",
            "Consumption correction is required",
        ),
    ],
)
def test_consumption_numeric_fields_are_required(
    field_name,
    expected_message,
):
    collections = copy.deepcopy(
        valid_collections()
    )
    collections["consumption_items"][0][
        field_name
    ] = None

    result = validate(collections)

    assert result["valid"] is False
    assert result["errors"][
        f"consumption_items[0].{field_name}"
    ] == [
        expected_message,
    ]


@pytest.mark.parametrize(
    (
        "field_name",
        "invalid_value",
        "expected_message",
    ),
    [
        (
            "previous_reading",
            "19 A19",
            "Previous reading is invalid",
        ),
        (
            "current_reading",
            "4 05A",
            "Current reading is invalid",
        ),
        (
            "difference",
            "-1",
            (
                "Consumption difference must be "
                "a non-negative decimal"
            ),
        ),
        (
            "correction",
            "-1",
            (
                "Consumption correction must be "
                "a non-negative decimal"
            ),
        ),
    ],
)
def test_invalid_consumption_numeric_fields_are_rejected(
    field_name,
    invalid_value,
    expected_message,
):
    collections = copy.deepcopy(
        valid_collections()
    )
    collections["consumption_items"][0][
        field_name
    ] = invalid_value

    result = validate(collections)

    assert result["valid"] is False

    error_path = (
        f"consumption_items[0].{field_name}"
    )

    assert expected_message in result["errors"][
        error_path
    ]


@pytest.mark.parametrize(
    "valid_reading",
    [
        "0",
        "60",
        "999",
        "3 991",
        "19 719",
        "1 234 567",
    ],
)
def test_reading_format_accepts_grouped_thousands(
    valid_reading,
):
    collections = copy.deepcopy(
        valid_collections()
    )
    item = collections["consumption_items"][0]

    item["previous_reading"] = valid_reading
    item["current_reading"] = valid_reading

    assert validate(collections)["valid"] is True
