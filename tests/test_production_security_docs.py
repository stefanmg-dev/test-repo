from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEPLOYMENT = PROJECT_ROOT / "docs" / "deployment.md"
SECURITY = PROJECT_ROOT / "docs" / "security.md"


def test_deployment_docs_describe_implemented_security_boundary():
    content = DEPLOYMENT.read_text(encoding="utf-8")

    assert "API-key and OIDC authentication" in content
    assert "scope-based authorization" in content
    assert "upload validation and resource limits" in content
    assert "configurable rate limiting" in content
    assert "security audit logging" in content
    assert "separate planned security packages" not in content


def test_security_docs_distinguish_controls_from_operational_decisions():
    content = SECURITY.read_text(encoding="utf-8")

    assert "## Implemented security controls" in content
    assert "## Remaining operational decisions" in content
    assert "SPDX SBOM generation" in content
    assert "asynchronous processing" in content
    assert "## Planned phases" not in content
