from pathlib import Path


API_REFERENCE = (
    Path(__file__).resolve().parent.parent
    / "docs"
    / "api-reference.md"
)


def profiles_section() -> str:
    content = API_REFERENCE.read_text(encoding="utf-8")
    start = content.index(
        "### POST `/api/v1/config/document-types/{document_type}/profiles/{profile_name}`"
    )
    end = content.index(
        "### POST `/api/v1/config/document-types/{document_type}/profiles/{profile_name}/collections/{collection_name}`",
        start,
    )
    return content[start:end]


def test_profiles_reference_documents_scope_and_shape():
    content = profiles_section()

    assert content.count("config:write") == 2
    assert "Legacy anonymous access" in content
    assert "`^[a-z][a-z0-9_]*$`" in content
    for field_name in (
        "profile",
        "fields",
        "collections",
        "summary_validations",
        "default_profile",
    ):
        assert f"`{field_name}`" in content


def test_profiles_reference_documents_conflicts_and_errors():
    content = profiles_section()

    assert "does not change `default_profile`" in content
    assert "non-default profile" in content
    assert "uses legacy configuration" in content
    assert "profile name already exists" in content
    assert "current `default_profile`" in content
    assert "`404`" in content
    assert "`409`" in content
    assert "`422`" in content
