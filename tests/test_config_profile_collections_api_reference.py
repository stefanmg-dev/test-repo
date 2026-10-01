from pathlib import Path


API_REFERENCE = (
    Path(__file__).resolve().parent.parent
    / "docs"
    / "api-reference.md"
)


def profile_collections_section() -> str:
    content = API_REFERENCE.read_text(encoding="utf-8")
    start = content.index(
        "### POST `/api/v1/config/document-types/{document_type}/profiles/{profile_name}/collections/{collection_name}`"
    )
    end = content.index(
        "### POST `/api/v1/config/document-types/{document_type}/profiles/{profile_name}/fields`",
        start,
    )
    return content[start:end]


def test_profile_collections_reference_documents_scope_and_models():
    content = profile_collections_section()
    assert content.count("config:write") == 6
    assert "Legacy anonymous access" in content
    assert "`DocumentCollectionModel`" in content
    assert "`DocumentFieldModel`" in content
    for field_name in (
        "document_type",
        "profile_name",
        "collection_name",
        "field_name",
        "collection",
        "field",
    ):
        assert f"`{field_name}`" in content


def test_profile_collections_reference_documents_errors():
    content = profile_collections_section()
    assert "optionally renaming" in content
    assert "uses legacy configuration" in content
    assert "referenced by a collection item validation" in content
    assert "`404`" in content
    assert "`409`" in content
    assert "`422`" in content
