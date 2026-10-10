from pathlib import Path


REFERENCE = Path("docs/api-reference.md")


def test_runtime_api_reference_documents_fields_and_examples():
    content = REFERENCE.read_text(encoding="utf-8")

    assert '### GET `/health`' in content
    assert '### GET `/ready`' in content
    for field in ("status", "database", "migrations", "revision"):
        assert f"`{field}`" in content
    assert '"status": "ok"' in content
    assert '"status": "ready"' in content
    assert '"status": "not_ready"' in content
    assert "**Example `503` response:**" in content
