from collection_validator import validate_collections


SERVICE_FIELDS = [
    {
        "name": "description",
        "type": "regex",
        "rule": r"^(.+)$",
        "validation": [
            {
                "type": "required",
                "message": "Service description is required",
            }
        ],
    }
]


def schema(cardinality):
    return {
        "services": {
            "cardinality": cardinality,
            "start_pattern": r"^Услуга",
            "fields": SERVICE_FIELDS,
        }
    }


def test_zero_or_more_accepts_empty_collection():
    result = validate_collections(
        collections={"services": []},
        collection_schemas=schema("zero_or_more"),
    )

    assert result == {
        "valid": True,
        "errors": {},
    }


def test_zero_or_more_accepts_populated_collection():
    result = validate_collections(
        collections={
            "services": [
                {
                    "description": "Услуга 1",
                }
            ]
        },
        collection_schemas=schema("zero_or_more"),
    )

    assert result == {
        "valid": True,
        "errors": {},
    }


def test_one_or_more_rejects_empty_collection():
    result = validate_collections(
        collections={"services": []},
        collection_schemas=schema("one_or_more"),
    )

    assert result == {
        "valid": False,
        "errors": {
            "_services": [
                "Collection must contain at least one item",
            ]
        },
    }


def test_one_or_more_accepts_populated_collection():
    result = validate_collections(
        collections={
            "services": [
                {
                    "description": "Услуга 1",
                }
            ]
        },
        collection_schemas=schema("one_or_more"),
    )

    assert result == {
        "valid": True,
        "errors": {},
    }


def test_cardinality_error_does_not_hide_item_errors():
    result = validate_collections(
        collections={
            "services": [
                {
                    "description": None,
                }
            ]
        },
        collection_schemas=schema("one_or_more"),
    )

    assert result == {
        "valid": False,
        "errors": {
            "services[0].description": [
                "Service description is required",
            ]
        },
    }
