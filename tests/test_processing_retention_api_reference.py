from pathlib import Path


API_REFERENCE = (
    Path(__file__).resolve().parent.parent
    / "docs"
    / "api-reference.md"
)


def retention_section() -> str:
    content = API_REFERENCE.read_text(encoding="utf-8")
    start = content.index(
        "### POST `/api/v1/processing-runs/retention-execute`"
    )
    end = content.index(
        "### GET `/api/v1/processing-runs/review-summary`",
        start,
    )
    return content[start:end]


def test_retention_reference_documents_security_boundary():
    content = retention_section()

    assert content.count("internal `admin` scope") >= 2
    assert "Tenant isolation" in content
    assert "Browser delegated scopes do not grant `admin`" in content
    assert "irreversible" in content
    assert "security audit metadata" in content


def test_retention_reference_documents_request_and_response_fields():
    content = retention_section()

    for field_name in (
        "confirmation",
        "limit",
        "retention_days",
        "cutoff",
        "deleted_count",
        "candidate_count",
        "oldest_candidate_completed_at",
        "newest_candidate_completed_at",
    ):
        assert f"`{field_name}`" in content

    assert "Exact value `DELETE`" in content
    assert "range `1..1000`" in content
    assert "deleted atomically" in content
    assert "Call preview before execution" in content
    assert "`401`" in content
    assert "`403`" in content
    assert "`422`" in content
