from pathlib import Path


API_REFERENCE = (
    Path(__file__).resolve().parent.parent
    / "docs"
    / "api-reference.md"
)


def common_fields_section() -> str:
    content = API_REFERENCE.read_text(encoding="utf-8")
    start = content.index(
        "### POST `/api/v1/config/document-types/{document_type}/common-fields`"
    )
    end = content.index(
        "### POST `/api/v1/config/document-types/{document_type}/fields`",
        start,
    )
    return content[start:end]


def test_common_fields_reference_documents_scope_and_uniqueness():
    content = common_fields_section()
    assert content.count("config:write") == 3
    assert "Legacy anonymous access" in content
    assert "unique across all common fields and all profile fields" in content
    assert "does not require a `default_profile`" in content
    assert "ignored during its own uniqueness check" in content


def test_common_fields_reference_documents_errors():
    content = common_fields_section()
    assert "`DocumentFieldModel`" in content
    assert "optionally renaming" in content
    assert "`404`" in content
    assert "`409`" in content
    assert "`422`" in content
