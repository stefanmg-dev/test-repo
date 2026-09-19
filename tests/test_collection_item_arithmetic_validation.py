import pytest

from collection_item_validator import (
    CollectionItemValidationError,
)
from collection_validator import validate_collections


SCHEMAS = {
    "consumption_items": {
        "cardinality": "zero_or_more",
        "fields": [],
        "item_validations": [
            {
                "type": "difference_equals",
                "minuend": "current_reading",
                "subtrahend": "previous_reading",
                "result": "difference",
                "message": (
                    "Difference must equal current "
                    "reading minus previous reading"
                ),
            }
        ],
    }
}


def validate(item):
    return validate_collections(
        collections={
            "consumption_items": [
                item,
            ],
        },
        collection_schemas=SCHEMAS,
    )


def test_accepts_consistent_day_readings():
    result = validate(
        {
            "previous_reading": "19 719",
            "current_reading": "19 929",
            "difference": "210",
        }
    )

    assert result == {
        "valid": True,
        "errors": {},
    }


def test_accepts_consistent_night_readings():
    result = validate(
        {
            "previous_reading": "3 991",
            "current_reading": "4 051",
            "difference": "60",
        }
    )

    assert result == {
        "valid": True,
        "errors": {},
    }


def test_rejects_inconsistent_difference():
    result = validate(
        {
            "previous_reading": "19 719",
            "current_reading": "19 929",
            "difference": "211",
        }
    )

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


def test_supports_decimal_comma_values():
    result = validate(
        {
            "previous_reading": "10,50",
            "current_reading": "12,75",
            "difference": "2,25",
        }
    )

    assert result == {
        "valid": True,
        "errors": {},
    }


@pytest.mark.parametrize(
    "missing_field",
    [
        "previous_reading",
        "current_reading",
        "difference",
    ],
)
def test_skips_rule_when_operand_is_missing(
    missing_field,
):
    item = {
        "previous_reading": "19 719",
        "current_reading": "19 929",
        "difference": "210",
    }
    item[missing_field] = None

    assert validate(item) == {
        "valid": True,
        "errors": {},
    }


def test_rejects_unsupported_item_validation_type():
    schemas = {
        "consumption_items": {
            "cardinality": "zero_or_more",
            "fields": [],
            "item_validations": [
                {
                    "type": "unsupported_rule",
                }
            ],
        }
    }

    with pytest.raises(
        CollectionItemValidationError,
        match=(
            "Unsupported collection item "
            "validation type"
        ),
    ):
        validate_collections(
            collections={
                "consumption_items": [
                    {
                        "difference": "210",
                    }
                ],
            },
            collection_schemas=schemas,
        )
