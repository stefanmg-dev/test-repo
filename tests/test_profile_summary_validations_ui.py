from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
HTML = ROOT / "ui" / "index.html"
JS = ROOT / "ui" / "ui.js"


def test_summary_validation_ui_is_profile_scoped():
    html = HTML.read_text(encoding="utf-8")
    js = JS.read_text(encoding="utf-8")

    assert 'id="summaryValidationSection"' in html
    assert 'id="summaryValidationList"' in html
    assert 'id="openAddSummaryValidationButton"' in html
    assert 'state.selectedFieldScope === "profile"' in js
    assert "renderSummaryValidations(config)" in js


def test_summary_validation_editor_matches_typed_model():
    content = JS.read_text(encoding="utf-8")

    assert '["collection_sum_equals_field"]' in content
    assert '"summaryValidationCollection"' in content
    assert '"summaryValidationItemField"' in content
    assert '"summaryValidationTargetField"' in content
    assert '"summaryValidationMessage"' in content


def test_summary_validation_editor_uses_profile_schema_options():
    content = JS.read_text(encoding="utf-8")

    assert "const collections = profile.collections || {}" in content
    assert "collections[collection.select.value]?.fields || []" in content
    assert "getProfileScalarFieldNames(config, profileName)" in content


def test_summary_validation_editor_uses_specialized_api():
    content = JS.read_text(encoding="utf-8")

    assert '+ "/summary-validations"' in content
    assert 'method: isEditing ? "PUT" : "POST"' in content
    assert 'body: JSON.stringify({ validation })' in content
    assert '{ method: "DELETE" }' in content
