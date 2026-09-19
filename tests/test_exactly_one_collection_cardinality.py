from collection_validator import validate_collections


FIELDS = [
    {
        "name": "description",
        "type": "constant",
        "value": "sample",
        "validation": [],
    }
]


SCHEMAS = {
    "services": {
        "cardinality": "exactly_one",
        "fields": FIELDS,
    }
}


def validate(items):
    return validate_collections(
        collections={
            "services": items,
        },
        collection_schemas=SCHEMAS,
    )


def test_exactly_one_rejects_empty_collection():
    result = validate([])

    assert result["valid"] is False
    assert "_services" in result["errors"]


def test_exactly_one_accepts_single_item():
    result = validate(
        [
            {
                "description": "Услуга 1",
            }
        ]
    )

    assert result == {
        "valid": True,
        "errors": {},
    }


def test_exactly_one_rejects_multiple_items():
    result = validate(
        [
            {
                "description": "Услуга 1",
            },
            {
                "description": "Услуга 2",
            },
        ]
    )

    assert result["valid"] is False
    assert "_services" in result["errors"]


def test_exactly_one_collection_error_is_not_item_error():
    result = validate([])

    error_paths = set(result["errors"])

    assert error_paths == {
        "_services",
    }
    assert not any(
        path.startswith("services[")
        for path in error_paths
    )
