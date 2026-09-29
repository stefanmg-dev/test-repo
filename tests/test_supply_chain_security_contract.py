from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
WORKFLOW = PROJECT_ROOT / ".github" / "workflows" / "security.yml"
DOCUMENTATION = PROJECT_ROOT / "docs" / "supply-chain-security.md"


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_security_workflow_has_expected_triggers_and_permissions():
    content = read(WORKFLOW)

    assert "pull_request:" in content
    assert "schedule:" in content
    assert "workflow_dispatch:" in content
    assert "contents: read" in content
    assert "cancel-in-progress: true" in content


def test_security_workflow_audits_locked_python_dependencies():
    content = read(WORKFLOW)

    assert "pip-audit==2.10.1" in content
    assert "pipenv requirements --dev" in content
    assert "python -m pip_audit" in content
    assert "security-requirements.txt" in content
    assert "continue-on-error" not in content


def test_security_workflow_audits_npm_lockfile_without_modifying_it():
    content = read(WORKFLOW)

    assert "npm audit --package-lock-only --audit-level=high" in content
    assert "npm audit fix" not in content


def test_dependency_review_is_pull_request_only_and_versioned():
    content = read(WORKFLOW)

    assert "if: github.event_name == 'pull_request'" in content
    assert "actions/dependency-review-action@v5.0.0" in content
    assert "fail-on-severity: high" in content


def test_sbom_is_spdx_json_artifact_and_action_is_versioned():
    content = read(WORKFLOW)

    assert "anchore/sbom-action@v0.24.2" in content
    assert "format: spdx-json" in content
    assert "document-processing-sbom.spdx.json" in content
    assert "upload-artifact: true" in content
    assert "if: github.event_name != 'pull_request'" in content


def test_supply_chain_policy_forbids_silent_ignores_and_auto_fixes():
    content = read(DOCUMENTATION)

    assert "Findings are not ignored automatically" in content
    assert "does not run `npm audit fix`" in content
    assert "Do not silently replace audit failures" in content
    assert "Deprecation warnings" in content
