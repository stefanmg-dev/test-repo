from pathlib import Path


API_REFERENCE = (
    Path(__file__).resolve().parent.parent
    / "docs"
    / "api-reference.md"
)


def default_profile_section():
    content = API_REFERENCE.read_text(encoding="utf-8")
    start = content.index(
        "### PUT `/api/v1/config/document-types/{document_type}/default-profile`"
    )
    end = content.index(
        "### POST `/api/v1/config/document-types/{document_type}/profiles/{profile_name}`",
        start,
    )
    return content[start:end]


def test_default_profile_reference_documents_contract():
    content = default_profile_section()
    assert "config:write" in content
    assert "UpdateDefaultProfileRequest" in content
    assert "`profile_name`" in content
    assert "changes only `default_profile`" in content
    assert "preserved" in content
    assert "idempotent" in content
    assert "`404`" in content
    assert "`409`" in content
    assert "`422`" in content
