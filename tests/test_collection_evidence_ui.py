from pathlib import Path


HTML = Path(__file__).resolve().parent.parent / "ui" / "test.html"
JS = Path(__file__).resolve().parent.parent / "ui" / "test.js"


def test_extraction_ui_has_collection_result_container():
    content = HTML.read_text(encoding="utf-8")
    assert 'id="resultCollections"' in content


def test_extraction_ui_renders_collection_items_and_evidence():
    content = JS.read_text(encoding="utf-8")
    assert "function renderCollections(" in content
    assert "body.collections || {}" in content
    assert "body.collection_evidence || {}" in content
    assert "body.collection_validation?.errors || {}" in content
    assert "collectionEvidence?.[collectionName]" in content
    assert "formatCollectionEvidence(evidence)" in content


def test_collection_evidence_ui_does_not_use_sensitive_metadata():
    content = JS.read_text(encoding="utf-8")
    assert "evidence.pattern" not in content
    assert "evidence.anchor" not in content
    assert "evidence.value" not in content
