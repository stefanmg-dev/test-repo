from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
SCRIPT = PROJECT_ROOT / "scripts" / "deployment_smoke.py"
DOCUMENTATION = PROJECT_ROOT / "docs" / "deployment-smoke-test.md"


def test_deployment_smoke_helper_is_read_only_and_https_only():
    content = SCRIPT.read_text(encoding="utf-8")

    assert 'method="GET"' in content
    assert 'startswith("https://")' in content
    for method in ("POST", "PUT", "PATCH", "DELETE"):
        assert f'method="{method}"' not in content


def test_deployment_runbook_has_release_gate_and_rollback_criteria():
    content = DOCUMENTATION.read_text(encoding="utf-8")

    assert "## Go criteria" in content
    assert "## No-go and rollback criteria" in content
    assert "Tenant-isolation smoke checklist" in content
    assert "Microsoft Entra browser smoke checklist" in content
    assert "Do not record API keys" in content
