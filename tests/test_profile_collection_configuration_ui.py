from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
JS = ROOT / "ui" / "ui.js"


def test_profile_collection_context_uses_selected_profile():
    content = JS.read_text(encoding="utf-8")

    assert "function getSelectedCollectionContext(config)" in content
    assert 'state.selectedFieldScope === "profile"' in content
    assert "config.profiles?.[profileName]?.collections || {}" in content
    assert "collections: config.collections || {}" in content


def test_profile_collection_endpoint_matches_api_contract():
    content = JS.read_text(encoding="utf-8")

    assert "profileName = null" in content
    assert "`/profiles/${encodeURIComponent(profileName)}`" in content
    assert "function collectionEndpoint(" in content
    assert "collectionName," in content
    assert "profileName" in content


def test_profile_collection_fields_reuse_document_editor():
    content = JS.read_text(encoding="utf-8")

    assert "collectionProfileName = null" in content
    assert "`/profiles/${encodeURIComponent(collectionProfileName)}`" in content
    assert "openFieldModal(null, name, profileName)" in content
    assert "openFieldModal(field, name, profileName)" in content
    assert "confirmDeleteField(field, name, profileName)" in content


def test_collection_view_refreshes_on_scope_and_profile_changes():
    content = JS.read_text(encoding="utf-8")

    assert content.count("renderCollections(config);") >= 3
