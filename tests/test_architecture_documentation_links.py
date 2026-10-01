from pathlib import Path


DOCS = Path(__file__).resolve().parent.parent / "docs"
OPERATIONAL_DOCS = (
    "architecture.md",
    "deployment.md",
    "security.md",
    "backup-restore.md",
    "deployment-smoke-test.md",
)


def test_architecture_links_to_operational_runbooks():
    content = (DOCS / "architecture.md").read_text(encoding="utf-8")
    for filename in OPERATIONAL_DOCS[1:]:
        assert f"]({filename})" in content
    assert "](development-quick-reference.md)" in content


def test_operational_runbooks_link_to_each_other():
    for filename in OPERATIONAL_DOCS[1:]:
        content = (DOCS / filename).read_text(encoding="utf-8")
        assert "## Related operational documentation" in content
        assert "](architecture.md)" in content
        for peer in OPERATIONAL_DOCS[1:]:
            if peer != filename:
                assert f"]({peer})" in content


def test_architecture_separates_implemented_and_operational_decisions():
    content = (DOCS / "architecture.md").read_text(encoding="utf-8")
    assert "## Production-readiness boundary" in content
    assert "Implemented runtime controls include" in content
    assert "deployment-specific decisions" in content
    assert "future asynchronous model remains outside" in content
