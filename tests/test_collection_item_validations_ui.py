from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
JS = ROOT / "ui" / "ui.js"


def test_collection_ui_exposes_item_validation_actions():
    content = JS.read_text(encoding="utf-8")

    assert '"Добави item validation"' in content
    assert '"Редактирай validation"' in content
    assert '"Изтрий validation"' in content
    assert "openItemValidationModal(" in content
    assert "confirmDeleteItemValidation(" in content


def test_item_validation_editor_matches_difference_equals_model():
    content = JS.read_text(encoding="utf-8")

    assert '["difference_equals"]' in content
    assert '"itemValidationMinuend"' in content
    assert '"itemValidationSubtrahend"' in content
    assert '"itemValidationResult"' in content
    assert '"itemValidationMessage"' in content


def test_item_validation_editor_uses_collection_field_names():
    content = JS.read_text(encoding="utf-8")

    assert "const fieldNames = (collection.fields || []).map(" in content
    assert "minuend: minuend.select.value" in content
    assert "subtrahend: subtrahend.select.value" in content
    assert "result: result.select.value" in content


def test_item_validation_updates_preserve_collection_scope():
    content = JS.read_text(encoding="utf-8")

    assert "async function saveCollectionDefinition(" in content
    assert "structuredClone(collection)" in content
    assert "profileName" in content
    assert 'body: JSON.stringify({ collection })' in content
