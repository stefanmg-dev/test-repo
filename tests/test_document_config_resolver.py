import pytest

from document_config_resolver import (
    DocumentConfigResolutionError,
    build_resolved_document_config,
    get_document_collections,
    resolve_document_fields,
)


def test_resolves_legacy_flat_fields():
    document_config = {
        "fields": [
            {
                "name": "invoice_number",
                "type": "regex",
            },
            {
                "name": "total_amount",
                "type": "regex",
            },
        ]
    }

    fields = resolve_document_fields(
        document_config
    )

    assert [
        field["name"]
        for field in fields
    ] == [
        "invoice_number",
        "total_amount",
    ]


def test_resolves_common_and_profile_fields():
    document_config = {
        "common_fields": [
            {
                "name": "invoice_number",
                "type": "regex",
            },
            {
                "name": "total_amount",
                "type": "regex",
            },
        ],
        "profiles": {
            "telecom_a1": {
                "fields": [
                    {
                        "name": "contract_number",
                        "type": "regex_list",
                    }
                ]
            }
        },
    }

    fields = resolve_document_fields(
        document_config=document_config,
        profile_name="telecom_a1",
    )

    assert [
        field["name"]
        for field in fields
    ] == [
        "invoice_number",
        "total_amount",
        "contract_number",
    ]


def test_profile_is_required_when_profiles_exist():
    document_config = {
        "common_fields": [],
        "profiles": {
            "telecom_a1": {
                "fields": []
            }
        },
    }

    with pytest.raises(
        DocumentConfigResolutionError,
        match="profile name is required",
    ):
        resolve_document_fields(
            document_config
        )


def test_unknown_profile_is_rejected():
    document_config = {
        "common_fields": [],
        "profiles": {
            "telecom_a1": {
                "fields": []
            }
        },
    }

    with pytest.raises(
        DocumentConfigResolutionError,
        match="was not found",
    ):
        resolve_document_fields(
            document_config=document_config,
            profile_name="electricity_evn",
        )


def test_profile_field_overrides_common_field():
    document_config = {
        "common_fields": [
            {
                "name": "supplier_name",
                "type": "llm",
            },
            {
                "name": "invoice_number",
                "type": "regex",
            },
        ],
        "profiles": {
            "telecom_a1": {
                "fields": [
                    {
                        "name": "supplier_name",
                        "type": "constant",
                        "value": "А1 България ЕАД",
                    },
                    {
                        "name": "contract_number",
                        "type": "regex_list",
                    },
                ]
            }
        },
    }

    fields = resolve_document_fields(
        document_config=document_config,
        profile_name="telecom_a1",
    )

    assert fields == [
        {
            "name": "supplier_name",
            "type": "constant",
            "value": "А1 България ЕАД",
        },
        {
            "name": "invoice_number",
            "type": "regex",
        },
        {
            "name": "contract_number",
            "type": "regex_list",
        },
    ]


def test_duplicate_fields_inside_profile_are_rejected():
    document_config = {
        "common_fields": [],
        "profiles": {
            "telecom_a1": {
                "fields": [
                    {
                        "name": "supplier_name",
                        "type": "constant",
                    },
                    {
                        "name": "supplier_name",
                        "type": "regex",
                    },
                ]
            }
        },
    }

    with pytest.raises(
        DocumentConfigResolutionError,
        match="Duplicate resolved field",
    ):
        resolve_document_fields(
            document_config=document_config,
            profile_name="telecom_a1",
        )


def test_builds_compatible_extraction_config():
    document_config = {
        "common_fields": [
            {
                "name": "invoice_number",
                "type": "regex",
            }
        ],
        "profiles": {
            "telecom_a1": {
                "fields": [
                    {
                        "name": "contract_number",
                        "type": "regex_list",
                    }
                ]
            }
        },
    }

    resolved_config = (
        build_resolved_document_config(
            document_config=document_config,
            profile_name="telecom_a1",
        )
    )

    assert resolved_config == {
        "fields": [
            {
                "name": "invoice_number",
                "type": "regex",
            },
            {
                "name": "contract_number",
                "type": "regex_list",
            },
        ]
    }


def test_resolver_returns_deep_copy():
    document_config = {
        "fields": [
            {
                "name": "invoice_number",
                "type": "regex",
                "validation": [
                    {
                        "type": "required",
                    }
                ],
            }
        ]
    }

    resolved_fields = resolve_document_fields(
        document_config
    )

    resolved_fields[0]["name"] = "changed"
    resolved_fields[0]["validation"][0][
        "type"
    ] = "changed"

    assert document_config["fields"][0][
        "name"
    ] == "invoice_number"

    assert document_config["fields"][0][
        "validation"
    ][0][
        "type"
    ] == "required"


def test_profile_is_rejected_for_legacy_config():
    document_config = {
        "fields": [
            {
                "name": "invoice_number",
                "type": "regex",
            }
        ]
    }

    with pytest.raises(
        DocumentConfigResolutionError,
        match="legacy document configuration",
    ):
        resolve_document_fields(
            document_config=document_config,
            profile_name="telecom_a1",
        )


def test_invalid_document_configuration_is_rejected():
    with pytest.raises(
        DocumentConfigResolutionError,
        match="must be an object",
    ):
        resolve_document_fields(
            None
        )


def test_field_without_name_is_rejected():
    document_config = {
        "fields": [
            {
                "type": "regex",
            }
        ]
    }

    with pytest.raises(
        DocumentConfigResolutionError,
        match="must have a name",
    ):
        resolve_document_fields(
            document_config
        )

def test_resolves_collection_schema_as_deep_copy():
    config = {"collections": {"meters": {"cardinality": "zero_or_more", "fields": []}}}
    collections = get_document_collections(config)
    collections["meters"]["fields"].append({"name": "meter_number"})
    assert config["collections"]["meters"]["fields"] == []


def test_build_includes_collections_when_configured():
    config = {
        "fields": [{"name": "invoice_number", "type": "regex"}],
        "collections": {"services": {"cardinality": "zero_or_more", "fields": []}},
    }
    resolved = build_resolved_document_config(config)
    assert resolved["collections"] == config["collections"]
    assert resolved["collections"] is not config["collections"]


@pytest.mark.parametrize(
    "cardinality",
    ["zero_or_more", "one_or_more", "exactly_one"],
)
def test_accepts_supported_collection_cardinality(cardinality):
    config = {
        "collections": {
            "meters": {
                "cardinality": cardinality,
                "fields": [],
            }
        }
    }

    assert get_document_collections(config) == config["collections"]


def test_rejects_unsupported_collection_cardinality():
    with pytest.raises(
        DocumentConfigResolutionError,
        match="unsupported cardinality: many",
    ):
        get_document_collections({
            "collections": {
                "meters": {
                    "cardinality": "many",
                    "fields": [],
                }
            }
        })


def test_rejects_non_object_collection_schema():
    with pytest.raises(
        DocumentConfigResolutionError,
        match="Collection 'meters' must be an object",
    ):
        get_document_collections({
            "collections": {"meters": []}
        })


def test_rejects_non_list_collection_fields():
    with pytest.raises(
        DocumentConfigResolutionError,
        match="Collection 'meters' fields must be a list",
    ):
        get_document_collections({
            "collections": {
                "meters": {"fields": {}}
            }
        })


def test_rejects_duplicate_collection_field_names():
    with pytest.raises(
        DocumentConfigResolutionError,
        match=(
            "Collection 'meters': Duplicate resolved "
            "field 'meter_number'"
        ),
    ):
        get_document_collections({
            "collections": {
                "meters": {
                    "fields": [
                        {"name": "meter_number"},
                        {"name": "meter_number"},
                    ]
                }
            }
        })


def test_rejects_invalid_profile_collection_schema():
    config = {
        "common_fields": [],
        "profiles": {
            "electricity_electrohold": {
                "fields": [],
                "collections": {
                    "meters": {
                        "cardinality": "many",
                        "fields": [],
                    }
                },
            }
        },
    }

    with pytest.raises(
        DocumentConfigResolutionError,
        match="unsupported cardinality: many",
    ):
        build_resolved_document_config(
            document_config=config,
            profile_name="electricity_electrohold",
        )
