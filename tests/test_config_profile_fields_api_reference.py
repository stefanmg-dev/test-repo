from pathlib import Path


API_REFERENCE = (
    Path(__file__).resolve().parent.parent
    / "docs"
    / "api-reference.md"
)


def profile_fields_section() -> str:
    content = API_REFERENCE.read_text(encoding="utf-8")
    start = content.index(
        "### POST `/api/v1/config/document-types/{document_type}/profiles/{profile_name}/fields`"
    )
    end = content.index(
        "### PUT `/api/v1/config/document-types/{document_type}/rename`",
        start,
    )
    return content[start:end]


def test_profile_fields_reference_documents_scope_and_uniqueness():
    content = profile_fields_section()
    assert content.count("config:write") == 3
    assert "Legacy anonymous access" in content
    assert "unique across every common field and every profile field" in content
    assert "ignored during its own uniqueness check" in content


def test_profile_fields_reference_documents_contract_and_errors():
    content = profile_fields_section()
    for field_name in (
        "document_type",
        "profile_name",
        "field_name",
        "field",
    ):
        assert f"`{field_name}`" in content

    assert "`DocumentFieldModel`" in content
    assert "optionally renaming" in content
    assert "`404`" in content
    assert "`409`" in content
    assert "`422`" in content
