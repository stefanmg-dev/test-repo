from pathlib import Path


API_REFERENCE = (
    Path(__file__).resolve().parent.parent
    / "docs"
    / "api-reference.md"
)


def legacy_fields_section() -> str:
    content = API_REFERENCE.read_text(encoding="utf-8")
    start = content.index(
        "### POST `/api/v1/config/document-types/{document_type}/fields`"
    )
    end = content.index(
        "### POST `/api/v1/config/document-types/{document_type}/profiles/{profile_name}`",
        start,
    )
    return content[start:end]


def test_legacy_field_reference_documents_scope_and_operations():
    content = legacy_fields_section()

    assert content.count("config:write") == 3
    assert "Legacy anonymous access" in content
    assert "Completely replace" in content
    assert "optionally renaming" in content
    assert "field.name" in content


def test_legacy_field_reference_documents_models_and_errors():
    content = legacy_fields_section()

    for field_name in (
        "name",
        "type",
        "label",
        "value",
        "rule",
        "rules",
        "anchor",
        "pattern",
        "direction",
        "window_size",
        "occurrence",
        "validation",
        "message",
        "format",
        "minimum",
        "maximum",
    ):
        assert f"`{field_name}`" in content

    assert "`constant`, `regex`, `regex_list`, `nearby`, or `llm`" in content
    assert "`required`, `regex`, `date`, and `decimal`" in content
    assert "`404`" in content
    assert "`409`" in content
    assert "`422`" in content
