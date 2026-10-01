from pathlib import Path


API_REFERENCE = (
    Path(__file__).resolve().parent.parent
    / "docs"
    / "api-reference.md"
)


def collections_section() -> str:
    content = API_REFERENCE.read_text(encoding="utf-8")
    start = content.index(
        "### POST `/api/v1/config/document-types/{document_type}/collections/{collection_name}`"
    )
    end = content.index(
        "### POST `/api/v1/config/document-types/{document_type}/common-fields`",
        start,
    )
    return content[start:end]


def test_collections_reference_documents_scope_and_models():
    content = collections_section()
    assert content.count("config:write") == 6
    assert "Legacy anonymous access" in content
    for field_name in (
        "collection",
        "cardinality",
        "start_pattern",
        "fields",
        "item_validations",
        "difference_equals",
        "result",
        "minuend",
        "subtrahend",
    ):
        assert f"`{field_name}`" in content


def test_collections_reference_documents_errors_and_invariants():
    content = collections_section()
    assert "Field names must be unique within the collection" in content
    assert "all referenced fields must exist" in content
    assert "optionally renaming" in content
    assert "referenced by a collection item validation" in content
    assert "`404`" in content
    assert "`409`" in content
    assert "`422`" in content
