import pytest

from collection_validator import (
    CollectionValidationError,
    validate_collections,
)


SCHEMAS = {
    "meters": {
        "fields": [
            {
                "name": "meter_number",
                "validation": [
                    {
                        "type": "required",
                        "message": "Meter number is required",
                    },
                    {
                        "type": "regex",
                        "pattern": r"[0-9]{10}",
                        "message": "Meter number is invalid",
                    },
                ],
            }
        ]
    },
    "consumption_items": {
        "fields": [
            {
                "name": "quantity",
                "validation": [
                    {
                        "type": "decimal",
                        "minimum": "0",
                        "message": "Quantity is invalid",
                    }
                ],
            }
        ]
    },
}


def test_validates_collection_items_successfully():
    assert validate_collections(
        collections={
            "meters": [{"meter_number": "1021015029"}],
            "consumption_items": [{"quantity": "210"}],
        },
        collection_schemas=SCHEMAS,
    ) == {"valid": True, "errors": {}}


def test_reports_exact_collection_item_paths():
    assert validate_collections(
        collections={
            "meters": [{"meter_number": None}],
            "consumption_items": [
                {"quantity": "210"},
                {"quantity": "invalid"},
            ],
        },
        collection_schemas=SCHEMAS,
    ) == {
        "valid": False,
        "errors": {
            "meters[0].meter_number": [
                "Meter number is required"
            ],
            "consumption_items[1].quantity": [
                "Quantity is invalid"
            ],
        },
    }


def test_empty_collections_are_valid():
    assert validate_collections(
        collections={"meters": []},
        collection_schemas=SCHEMAS,
    ) == {"valid": True, "errors": {}}


def test_rejects_invalid_collections_container():
    with pytest.raises(
        CollectionValidationError,
        match="Collections must be an object",
    ):
        validate_collections([], SCHEMAS)
