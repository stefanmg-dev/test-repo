import pytest

from collection_summary_validator import (
    CollectionSummaryValidationError,
    validate_collection_summaries,
)


RULE = {
    "type": "collection_sum_equals_field",
    "collection": "consumption_items",
    "item_field": "quantity",
    "target_field": "total_consumption",
    "message": (
        "Consumption item quantities must equal "
        "total consumption"
    ),
}


def validate(fields, collections):
    return validate_collection_summaries(
        fields=fields,
        collections=collections,
        validations=[RULE],
    )


def test_accepts_matching_collection_sum():
    result = validate(
        fields={
            "total_consumption": "270",
        },
        collections={
            "consumption_items": [
                {"quantity": "210"},
                {"quantity": "60"},
            ],
        },
    )

    assert result == {
        "valid": True,
        "errors": {},
    }


def test_rejects_mismatched_collection_sum():
    result = validate(
        fields={
            "total_consumption": "271",
        },
        collections={
            "consumption_items": [
                {"quantity": "210"},
                {"quantity": "60"},
            ],
        },
    )

    assert result == {
        "valid": False,
        "errors": {
            "_summary.total_consumption": [
                (
                    "Consumption item quantities "
                    "must equal total consumption"
                ),
            ]
        },
    }


def test_supports_decimal_comma_and_grouped_values():
    result = validate(
        fields={
            "total_consumption": "1 270,50",
        },
        collections={
            "consumption_items": [
                {"quantity": "1 200,25"},
                {"quantity": "70,25"},
            ],
        },
    )

    assert result == {
        "valid": True,
        "errors": {},
    }


@pytest.mark.parametrize(
    (
        "fields",
        "collections",
    ),
    [
        (
            {"total_consumption": None},
            {
                "consumption_items": [
                    {"quantity": "210"},
                ],
            },
        ),
        (
            {"total_consumption": "270"},
            {
                "consumption_items": [
                    {"quantity": None},
                ],
            },
        ),
        (
            {"total_consumption": "270"},
            {
                "consumption_items": [
                    {"quantity": "invalid"},
                ],
            },
        ),
    ],
)
def test_skips_summary_when_dependency_is_invalid(
    fields,
    collections,
):
    assert validate(fields, collections) == {
        "valid": True,
        "errors": {},
    }


def test_empty_collection_sum_can_equal_zero():
    result = validate(
        fields={
            "total_consumption": "0",
        },
        collections={
            "consumption_items": [],
        },
    )

    assert result == {
        "valid": True,
        "errors": {},
    }


def test_rejects_unsupported_summary_rule():
    with pytest.raises(
        CollectionSummaryValidationError,
        match="Unsupported summary validation type",
    ):
        validate_collection_summaries(
            fields={},
            collections={},
            validations=[
                {
                    "type": "unsupported_rule",
                }
            ],
        )
