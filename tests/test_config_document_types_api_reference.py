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


def test_core_document_type_reference_documents_models_and_scopes():
    content = section(
        "### GET `/api/v1/config/document-types`",
        "### POST `/api/v1/config/document-types/{document_type}/collections/{collection_name}`",
    )

    assert "config:read" in content
    assert "config:write" in content
    assert "Legacy anonymous access" in content
    for field_name in (
        "document_types",
        "resolved_document_types",
        "document_type_metadata",
        "profile",
        "fields",
        "status",
        "ready",
        "field_count",
        "document_type",
        "configuration_mode",
    ):
        assert f"`{field_name}`" in content

    assert "`404`" in content
    assert "`409`" in content
    assert "`422`" in content


def test_document_type_rename_reference_documents_contract():
    content = section(
        "### PUT `/api/v1/config/document-types/{document_type}/rename`",
        "### GET `/api/v1/processing-runs`",
    )

    assert "config:write" in content
    assert "`new_document_type`" in content
    assert "idempotent successful operation" in content
    assert "`404`" in content
    assert "`409`" in content
    assert "`422`" in content
