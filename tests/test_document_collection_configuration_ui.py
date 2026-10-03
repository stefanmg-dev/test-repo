from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
HTML = ROOT / "ui" / "index.html"
JS = ROOT / "ui" / "ui.js"


def test_configuration_ui_exposes_document_collection_editor():
    html = HTML.read_text(encoding="utf-8")
    js = JS.read_text(encoding="utf-8")

    assert 'id="openAddCollectionButton"' in html
    assert 'id="collectionList"' in html
    assert "function renderCollections(config)" in js
    assert "function openCollectionModal(" in js
    assert "function confirmDeleteCollection(" in js


def test_collection_editor_uses_document_collection_api_contract():
    content = JS.read_text(encoding="utf-8")

    assert "/collections/${encodeURIComponent(collectionName)}" in content
    assert 'method: isEditing ? "PUT" : "POST"' in content
    assert '{ method: "DELETE" }' in content
    assert "body: JSON.stringify({ collection })" in content


def test_collection_editor_supports_schema_fields_and_preserves_children():
    content = JS.read_text(encoding="utf-8")

    for cardinality in (
        "zero_or_more",
        "one_or_more",
        "exactly_one",
    ):
        assert cardinality in content

    assert "collection.start_pattern = startPattern" in content
    assert "existingCollection?.fields || []" in content
    assert "existingCollection?.item_validations || []" in content
    assert "name.input.disabled = isEditing" in content


def test_collection_editor_supports_document_and_profile_scopes():
    content = JS.read_text(encoding="utf-8")

    collection_editor = content[
        content.index("function collectionEndpoint("):
        content.index("function selectDocumentType(")
    ]

    assert "config.collections || {}" in collection_editor
    assert "config.profiles?.[profileName]?.collections || {}" in collection_editor
    assert "/profiles/${" in collection_editor
