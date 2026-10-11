from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEPLOYMENT = ROOT / "docs" / "deployment.md"


def test_deployment_documents_guarded_operational_ui_workflows():
    content = DEPLOYMENT.read_text(encoding="utf-8")

    for required in (
        "/ui/index.html",
        "Провери snapshot",
        "successful dry-run",
        "`RESTORE`",
        "/ui/history.html",
        "Провери retention",
        "Изпълни retention",
        "1 through 1000",
        "`DELETE`",
        "internal `admin` scope",
        "destructive",
    ):
        assert required in content

    assert content.index("Провери snapshot") < content.index("`RESTORE`")
    assert content.index("Провери retention") < content.index("`DELETE`")
