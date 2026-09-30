from pathlib import Path


API_REFERENCE = (
    Path(__file__).resolve().parent.parent
    / "docs"
    / "api-reference.md"
)


def review_section() -> str:
    content = API_REFERENCE.read_text(encoding="utf-8")
    start = content.index(
        "### GET `/api/v1/processing-runs/{run_id}/review`"
    )
    end = content.index(
        "### GET `/api/v1/processing-runs/{run_id}/universal-invoice`",
        start,
    )
    return content[start:end]


def test_review_reference_documents_access_and_tenant_boundary():
    content = review_section()

    assert content.count("processing-runs:review") == 2
    assert "Tenant isolation" in content
    assert "attributed to the authenticated principal" in content
    assert "`run_id` (UUID, required)" in content


def test_review_reference_explains_request_and_response_fields():
    content = review_section()

    for field_name in (
        "processing_run_id",
        "status",
        "original_values",
        "corrected_values",
        "effective_values",
        "comment",
        "reviewed_at",
        "reviewed_by_type",
        "reviewed_by_subject",
    ):
        assert f"`{field_name}`" in content

    assert "maximum 2000 characters" in content
    assert "`approved`, `corrected`, or `rejected`" in content
    assert "`404`" in content
    assert "`409`" in content
    assert "`422`" in content
