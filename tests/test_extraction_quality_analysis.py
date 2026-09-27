from extraction_quality_analysis import (
    compare_extracted_fields,
)


def test_compares_changed_unchanged_added_and_removed_fields():
    result = compare_extracted_fields(
        original_values={
            "invoice_number": "100",
            "supplier_name": "A1",
            "removed_field": "old",
        },
        corrected_values={
            "invoice_number": "101",
            "supplier_name": "A1",
            "added_field": "new",
        },
    )

    assert result["counts"] == {
        "total": 4,
        "unchanged": 1,
        "changed": 1,
        "added": 1,
        "removed": 1,
    }
    assert result["changed_total"] == 3
    assert result["correction_rate"] == 0.75

    fields = {
        field["field_name"]: field
        for field in result["fields"]
    }

    assert fields["invoice_number"] == {
        "field_name": "invoice_number",
        "status": "changed",
        "original_value": "100",
        "corrected_value": "101",
    }
    assert fields["supplier_name"]["status"] == "unchanged"
    assert fields["added_field"] == {
        "field_name": "added_field",
        "status": "added",
        "original_value": None,
        "corrected_value": "new",
    }
    assert fields["removed_field"] == {
        "field_name": "removed_field",
        "status": "removed",
        "original_value": "old",
        "corrected_value": None,
    }


def test_distinguishes_missing_field_from_explicit_null():
    result = compare_extracted_fields(
        original_values={
            "kept_null": None,
            "removed_null": None,
        },
        corrected_values={
            "kept_null": None,
            "added_null": None,
        },
    )

    fields = {
        field["field_name"]: field
        for field in result["fields"]
    }

    assert fields["kept_null"]["status"] == "unchanged"
    assert fields["removed_null"]["status"] == "removed"
    assert fields["added_null"]["status"] == "added"


def test_compares_nested_json_values_without_mutating_inputs():
    original = {
        "metadata": {
            "numbers": [1, 2],
        }
    }
    corrected = {
        "metadata": {
            "numbers": [1, 3],
        }
    }

    result = compare_extracted_fields(
        original_values=original,
        corrected_values=corrected,
    )

    assert result["counts"]["changed"] == 1
    assert original == {
        "metadata": {
            "numbers": [1, 2],
        }
    }
    assert corrected == {
        "metadata": {
            "numbers": [1, 3],
        }
    }


def test_empty_values_have_zero_correction_rate():
    result = compare_extracted_fields(
        original_values={},
        corrected_values={},
    )

    assert result == {
        "counts": {
            "total": 0,
            "unchanged": 0,
            "changed": 0,
            "added": 0,
            "removed": 0,
        },
        "changed_total": 0,
        "correction_rate": 0.0,
        "fields": [],
    }


def test_aggregates_quality_by_configuration_identity():
    from extraction_quality_analysis import (
        aggregate_quality_analysis,
    )

    result = aggregate_quality_analysis(
        [
            {
                "document_type": "invoice",
                "profile": "telecom_a1",
                "configuration_hash": "hash-a",
                "original_values": {
                    "invoice_number": "100",
                    "supplier_name": "A1",
                },
                "corrected_values": {
                    "invoice_number": "101",
                    "supplier_name": "A1",
                },
            },
            {
                "document_type": "invoice",
                "profile": "telecom_a1",
                "configuration_hash": "hash-a",
                "original_values": {
                    "invoice_number": "200",
                    "total_amount": "20.00",
                },
                "corrected_values": {
                    "invoice_number": "201",
                    "total_amount": "21.00",
                },
            },
            {
                "document_type": "invoice",
                "profile": "electricity_electrohold",
                "configuration_hash": "hash-b",
                "original_values": {"total_amount": "30.00"},
                "corrected_values": {"total_amount": "31.00"},
            },
        ]
    )

    assert result["corrected_runs"] == 3
    assert len(result["groups"]) == 2

    a1 = next(
        group
        for group in result["groups"]
        if group["profile"] == "telecom_a1"
        and group["configuration_hash"] == "hash-a"
    )
    assert a1["corrected_runs"] == 2
    assert a1["field_counts"] == {
        "total": 4,
        "unchanged": 1,
        "changed": 3,
        "added": 0,
        "removed": 0,
    }
    assert a1["corrections"] == 3
    assert a1["correction_rate"] == 0.75
    assert a1["field_corrections"] == [
        {
            "field_name": "invoice_number",
            "corrections": 2,
        },
        {
            "field_name": "total_amount",
            "corrections": 1,
        },
    ]


def test_empty_quality_analysis_has_no_groups():
    from extraction_quality_analysis import (
        aggregate_quality_analysis,
    )

    assert aggregate_quality_analysis([]) == {
        "corrected_runs": 0,
        "groups": [],
    }
