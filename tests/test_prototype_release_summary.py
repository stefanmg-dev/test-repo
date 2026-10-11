from pathlib import Path


SUMMARY = (
    Path(__file__).resolve().parent.parent
    / "docs"
    / "prototype-release-summary.md"
)


def test_release_summary_records_checkpoint_and_evidence():
    content = SUMMARY.read_text(encoding="utf-8")
    assert "`de5f161`" in content
    assert "1212 passed tests" in content
    assert "5 intentionally skipped" in content
    assert "GitHub Actions CI run #181" in content
    assert "Supply Chain Security run #106" in content
    assert "no pending Alembic upgrade operations" in content
    assert "unchanged OpenAPI export" in content


def test_release_summary_documents_scope_and_boundaries():
    content = SUMMARY.read_text(encoding="utf-8")
    assert "## Implemented prototype capabilities" in content
    assert "## Current boundaries" in content
    assert "## Deferred architecture" in content
    assert "Processing remains synchronous" in content
    assert "HEIF and HEIC are outside" in content
    assert "Asynchronous processing with `202 Accepted`" in content


def test_release_summary_links_operational_documentation():
    content = SUMMARY.read_text(encoding="utf-8")
    for filename in (
        "architecture.md",
        "deployment.md",
        "security.md",
        "backup-restore.md",
        "deployment-smoke-test.md",
        "development-quick-reference.md",
        "api-reference.md",
    ):
        assert f"]({filename})" in content


def test_release_summary_records_operational_handoff_closure():
    content = SUMMARY.read_text(encoding="utf-8")

    for required in (
        "guarded configuration snapshot recovery",
        "guarded processing retention",
        "deployment-owner cutover checklist",
        "does not approve a production cutover",
        "deployment smoke test",
    ):
        assert required in content
