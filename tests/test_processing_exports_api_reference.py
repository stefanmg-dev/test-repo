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


def test_csv_export_reference_documents_columns_and_safety():
    content = section(
        "### GET `/api/v1/processing-runs/export`",
        "### GET `/api/v1/processing-runs/extraction-quality`",
    )

    assert "processing-runs:read" in content
    assert "text/csv; charset=utf-8" in content
    assert "processing-runs.csv" in content
    for column in (
        "processing_run_id",
        "document_type",
        "profile",
        "filename",
        "processing_status",
        "review_status",
        "created_at",
        "completed_at",
        "reviewed_at",
        "configuration_hash",
        "effective_values_json",
    ):
        assert f"`{column}`" in content

    assert "excludes raw OCR text" in content
    assert "formula-injection" in content


def test_feedback_export_reference_documents_cursor_and_records():
    content = section(
        "### GET `/api/v1/processing-runs/universal-invoice-feedback-export`",
        "### GET `/api/v1/processing-runs/{run_id}`",
    )

    assert "processing-runs:read" in content
    assert "application/x-ndjson" in content
    assert "range `1..1000`" in content
    assert "Both cursor components must be supplied together" in content
    for field_name in (
        "feedback_schema_version",
        "processing_run_id",
        "configuration_hash",
        "invoice_schema_version",
        "review_status",
        "reviewed_at",
        "reviewed_by_type",
        "original_universal_invoice",
        "reviewed_universal_invoice",
        "X-Next-Reviewed-At",
        "X-Next-Processing-Run-Id",
    ):
        assert f"`{field_name}`" in content

    assert "excludes filenames and raw OCR text" in content
    assert "no partial JSONL records" in content
    assert "`409`" in content
    assert "`422`" in content
