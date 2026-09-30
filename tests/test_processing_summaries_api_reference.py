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


def test_extraction_quality_and_shadow_reference_document_contracts():
    content = section(
        "### GET `/api/v1/processing-runs/extraction-quality`",
        "### POST `/api/v1/processing-runs/retention-execute`",
    )

    assert content.count("processing-runs:read") == 2
    assert content.count("tenant-isolated") == 2
    assert "does not return document values" in content
    for field_name in (
        "corrected_runs",
        "groups",
        "document_type",
        "profile",
        "configuration_hash",
        "field_counts",
        "corrections",
        "correction_rate",
        "field_corrections",
        "total",
        "succeeded",
        "failed",
        "not_applicable",
        "success_rate",
        "schema_versions",
        "failure_reasons",
        "schema_version",
        "reason",
        "count",
    ):
        assert f"`{field_name}`" in content


def test_review_summary_reference_documents_nullable_duration():
    content = section(
        "### GET `/api/v1/processing-runs/review-summary`",
        "### GET `/api/v1/processing-runs/universal-invoice-feedback-export`",
    )

    assert "processing-runs:read" in content
    assert "tenant-isolated" in content
    for field_name in (
        "total_requiring_review",
        "pending",
        "approved",
        "corrected",
        "rejected",
        "average_review_duration_ms",
    ):
        assert f"`{field_name}`" in content

    assert "or `null` when no completed reviews are available" in content
