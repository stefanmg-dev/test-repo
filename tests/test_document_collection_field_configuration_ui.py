from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
JS = ROOT / "ui" / "ui.js"


def test_collection_renderer_exposes_collection_field_actions():
    content = JS.read_text(encoding="utf-8")

    assert '"Добави поле в колекцията"' in content
    assert '"Редактирай поле"' in content
    assert '"Изтрий поле"' in content
    assert "openFieldModal(null, name, profileName)" in content
    assert "openFieldModal(field, name, profileName)" in content
    assert "confirmDeleteField(field, name, profileName)" in content


def test_field_endpoint_supports_document_collection_scope():
    content = JS.read_text(encoding="utf-8")

    assert "collectionName = null" in content
    assert "if (collectionName)" in content
    assert "/collections/${encodeURIComponent(collectionName)}" in content
    assert '+ "/fields"' in content
    assert "collectionName" in content


def test_collection_fields_reuse_structured_field_editor():
    content = JS.read_text(encoding="utf-8")

    assert "function openFieldModal(" in content
    assert "buildFieldPayload(form, existingField)" in content
    assert "function confirmDeleteField(" in content
    assert "collectionName = null" in content
    assert "collectionProfileName = null" in content
    assert 'body: JSON.stringify({ field })' in content


def test_collection_field_editor_supports_document_and_profile_scopes():
    content = JS.read_text(encoding="utf-8")
    start = content.index("function collectionEndpoint(")
    end = content.index("function selectDocumentType(")
    collection_editor = content[start:end]

    assert "config.collections || {}" in collection_editor
    assert "config.profiles?.[profileName]?.collections || {}" in collection_editor
    assert "/profiles/${" in collection_editor
