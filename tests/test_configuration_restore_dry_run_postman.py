import json
from pathlib import Path


COLLECTION = Path(
    "postman/Document_Processing_API_Stable.postman_collection.json"
)


def get_dry_run_request():
    collection = json.loads(COLLECTION.read_text(encoding="utf-8"))
    folder = next(
        item
        for item in collection["item"]
        if item["name"] == "05 Configuration Recovery"
    )
    return next(
        item
        for item in folder["item"]
        if item["name"] == "Validate Configuration Restore Candidate"
    )


def test_postman_contains_configuration_restore_dry_run_request():
    item = get_dry_run_request()

    assert item["request"]["method"] == "POST"
    assert item["request"]["url"]["raw"] == (
        "{{baseUrl}}/api/v1/config/restore/dry-run"
    )
    assert item["request"]["url"]["path"] == [
        "api",
        "v1",
        "config",
        "restore",
        "dry-run",
    ]
    assert "read-only" in item["request"]["description"]
    assert "never writes configuration" in item["request"]["description"]


def test_postman_dry_run_request_has_snapshot_body_and_checks():
    item = get_dry_run_request()
    raw = item["request"]["body"]["raw"]
    script = "\n".join(item["event"][0]["script"]["exec"])

    assert "schema_version" in raw
    assert "configurationSnapshotRevision" in raw
    assert "configurationSnapshotConfiguration" in raw
    assert "pm.response.to.have.status(200)" in script
    assert "body.snapshot_revision" in script
    assert "body.current_revision" in script
    assert "body.changes_detected" in script
