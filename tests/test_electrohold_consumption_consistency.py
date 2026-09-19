import copy

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
            },
            {
                "tariff": "Нощна",
                "previous_reading": "3 991",
                "current_reading": "4 051",
                "difference": "60",
                "correction": "0",
                "quantity": "60",
                "unit": "kWh",
            },
        ],
    }


def validate(collections):
    return validate_collections(
        collections=collections,
        collection_schemas=schemas(),
    )


def test_real_electrohold_readings_are_consistent():
    assert validate(valid_collections()) == {
        "valid": True,
        "errors": {},
    }


def test_inconsistent_day_difference_is_rejected():
    collections = copy.deepcopy(
        valid_collections()
    )
    collections["consumption_items"][0][
        "difference"
    ] = "211"

    result = validate(collections)

    assert result == {
        "valid": False,
        "errors": {
            "consumption_items[0]": [
                (
                    "Difference must equal current "
                    "reading minus previous reading"
                ),
            ]
        },
    }


def test_inconsistent_night_difference_is_rejected():
    collections = copy.deepcopy(
        valid_collections()
    )
    collections["consumption_items"][1][
        "current_reading"
    ] = "4 050"

    result = validate(collections)

    assert result == {
        "valid": False,
        "errors": {
            "consumption_items[1]": [
                (
                    "Difference must equal current "
                    "reading minus previous reading"
                ),
            ]
        },
    }
