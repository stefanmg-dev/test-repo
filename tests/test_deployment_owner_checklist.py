from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEPLOYMENT = ROOT / "docs" / "deployment.md"


def test_deployment_owner_cutover_checklist_covers_external_decisions():
    content = DEPLOYMENT.read_text(encoding="utf-8")

    assert "## Deployment-owner production cutover checklist" in content
    for required in (
        "Infrastructure sizing",
        "Concurrency limits",
        "request timeout policy",
        "Shared rate-limit storage",
        "Monitoring signals",
        "alert thresholds",
        "Incident ownership",
        "Database backup schedule",
        "RPO and RTO",
        "restore exercise",
        "previous known-good image",
        "production deployment smoke test",
        "no-go",
        "deployment-owner approval",
    ):
        assert required in content

    assert "do not replace deployment-owner approval" in content
