from configuration_identity import (
    CONFIGURATION_SCHEMA_VERSION,
    build_configuration_snapshot,
    canonical_configuration_json,
    configuration_sha256,
)


def test_snapshot_preserves_resolved_execution_context():
    fields = [{"name": "invoice_number", "type": "regex"}]
    collections = {
        "services": {
            "fields": [{"name": "description"}],
        }
    }
    validations = [
        {
            "type": "sum_equals",
            "collection": "services",
        }
    ]

    snapshot = build_configuration_snapshot(
        document_type="invoice",
        selected_profile="telecom_a1",
        resolved_fields=fields,
        resolved_collections=collections,
        resolved_summary_validations=validations,
    )

    assert snapshot == {
        "schema_version": CONFIGURATION_SCHEMA_VERSION,
        "document_type": "invoice",
        "selected_profile": "telecom_a1",
        "resolved_fields": fields,
        "resolved_collections": collections,
        "resolved_summary_validations": validations,
    }

    fields[0]["name"] = "changed"
    collections["services"]["fields"].clear()
    validations.clear()

    assert snapshot["resolved_fields"][0]["name"] == (
        "invoice_number"
    )
    assert snapshot["resolved_collections"]["services"][
        "fields"
    ] == [{"name": "description"}]
    assert len(
        snapshot["resolved_summary_validations"]
    ) == 1


def test_hash_is_independent_of_dictionary_key_order():
    first = {
        "schema_version": "1",
        "document_type": "invoice",
        "resolved_fields": [
            {
                "name": "invoice_number",
                "type": "regex",
            }
        ],
    }
    second = {
        "resolved_fields": [
            {
                "type": "regex",
                "name": "invoice_number",
            }
        ],
        "document_type": "invoice",
        "schema_version": "1",
    }

    assert canonical_configuration_json(first) == (
        canonical_configuration_json(second)
    )
    assert configuration_sha256(first) == (
        configuration_sha256(second)
    )


def test_hash_changes_when_resolved_configuration_changes():
    original = {
        "schema_version": "1",
        "resolved_fields": [{"name": "invoice_number"}],
    }
    changed = {
        "schema_version": "1",
        "resolved_fields": [{"name": "total_amount"}],
    }

    assert configuration_sha256(original) != (
        configuration_sha256(changed)
    )
    assert len(configuration_sha256(original)) == 64


def test_configuration_hash_is_valid_sha256_hex():
    snapshot = build_configuration_snapshot(
        document_type="invoice",
        selected_profile=None,
        resolved_fields=[],
        resolved_collections={},
        resolved_summary_validations=[],
    )

    digest = configuration_sha256(snapshot)

    assert len(digest) == 64
    assert int(digest, 16) >= 0
