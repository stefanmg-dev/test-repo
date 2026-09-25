from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_production_template_documents_complete_browser_scope_set():
    template = read(".env.production.example")
    assert "OIDC_BROWSER_CLIENT_ID=your-spa-application-client-id" in template
    assert "OIDC_BROWSER_AUTHORITY=https://login.microsoftonline.com/your-tenant-id" in template
    assert "OIDC_BROWSER_REDIRECT_PATH=/ui/index.html" in template
    for scope in (
        "documents.extract",
        "processing-runs.read",
        "config.read",
        "config.write",
    ):
        assert f"api://your-api-application-client-id/{scope}" in template
    assert "api://your-api-application-client-id/admin" not in template
    assert "LEGACY_ANONYMOUS_ACCESS_ENABLED=true" in template


def test_deployment_documentation_has_safe_cutover_gate():
    deployment = read("docs/deployment.md")
    security = read("docs/security.md")
    assert "## Microsoft Entra production cutover" in deployment
    assert "Single-page application" in deployment
    assert "LEGACY_ANONYMOUS_ACCESS_ENABLED=false" in deployment
    assert "protected routes return HTTP 401" in deployment
    assert "## OIDC delegated scope boundary" in security
    assert "Unknown delegated scopes are ignored" in security
    assert "admin` permission is not granted" in security
