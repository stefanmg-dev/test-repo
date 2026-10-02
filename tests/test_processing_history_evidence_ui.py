from pathlib import Path


HISTORY_JS = (
    Path(__file__).resolve().parent.parent
    / "ui"
    / "history.js"
)


def test_processing_history_renders_persisted_extraction_evidence():
    content = HISTORY_JS.read_text(encoding="utf-8")

    assert '"Evidence за полета"' in content
    assert "body.field_evidence" in content
    assert '"Evidence за колекции"' in content
    assert "body.collection_evidence" in content


def test_history_evidence_stays_separate_from_review_values():
    content = HISTORY_JS.read_text(encoding="utf-8")

    field_position = content.index("body.field_evidence")
    review_position = content.index("body.review_status")
    collection_position = content.index("body.collection_evidence")
    validation_position = content.index("body.validation")

    assert field_position < review_position
    assert collection_position < validation_position
