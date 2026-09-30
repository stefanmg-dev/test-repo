from pathlib import Path


API_REFERENCE = (
    Path(__file__).resolve().parent.parent
    / "docs"
    / "api-reference.md"
)


def extraction_section() -> str:
    content = API_REFERENCE.read_text(encoding="utf-8")
    start = content.index("### POST `/extract-document`")
    end = content.index("### GET `/health`", start)
    return content[start:end]


def test_extraction_reference_documents_external_consumer_contract():
    content = extraction_section()

    assert "documents:extract" in content
    assert "multipart/form-data" in content
    assert "`document_type` (string, required)" in content
    assert "`file` (binary, required)" in content
    assert "tenant-aware processing run" in content


def test_extraction_reference_explains_response_semantics():
    content = extraction_section()

    for field_name in (
        "processing_status",
        "profile",
        "quality",
        "raw_text",
        "llm_values",
        "final_values",
        "collections",
        "validation",
        "collection_validation",
    ):
        assert f"`{field_name}`:" in content

    assert "can contain sensitive document content" in content
    assert "`404`" in content
    assert "`409`" in content
    assert "`413`" in content
    assert "`415`" in content
    assert "`422`" in content
