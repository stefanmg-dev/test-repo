from pathlib import Path


API_REFERENCE = (
    Path(__file__).resolve().parent.parent
    / "docs"
    / "api-reference.md"
)


def section(start_heading: str, end_heading: str) -> str:
    content = API_REFERENCE.read_text(encoding="utf-8")
    start = content.index(start_heading)
    end = content.index(end_heading, start)
    return content[start:end]


def test_processing_run_list_reference_documents_contract():
    content = section(
        "### GET `/api/v1/processing-runs`",
        "### GET `/api/v1/processing-runs/export`",
    )

    assert "processing-runs:read" in content
    assert "tenant-isolated" in content
    assert "AND semantics" in content
    assert "range `1..100`" in content
    assert "Extracted document values are intentionally omitted" in content
    for parameter in (
        "offset",
        "limit",
        "document_type",
        "processing_status",
        "profile",
        "requires_review",
        "review_status",
        "invoice_shadow_validation_status",
        "invoice_schema_version",
    ):
        assert f"`{parameter}`" in content


def test_processing_run_detail_reference_documents_contract():
    content = section(
        "### GET `/api/v1/processing-runs/{run_id}`",
        "### GET `/api/v1/processing-runs/{run_id}/review`",
    )

    assert "processing-runs:read" in content
    assert "`run_id` (UUID, required)" in content
    assert "another tenant is not returned" in content
    for field_name in (
        "step_timings",
        "quality",
        "final_values",
        "field_evidence",
        "corrected_values",
        "configuration_hash",
        "configuration_snapshot",
        "configuration_schema_version",
        "invoice_schema_version",
        "invoice_shadow_validation_status",
        "invoice_shadow_validation_reason",
        "collections",
        "collection_evidence",
        "validation",
        "error",
        "updated_at",
    ):
        assert f"`{field_name}`" in content

    assert "`404`" in content
    assert "`422`" in content
