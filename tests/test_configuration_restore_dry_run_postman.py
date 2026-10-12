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
        "{{base_url}}/api/v1/config/restore/dry-run"
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


def test_postman_dry_run_requires_snapshot_and_stores_current_revision():
    item = get_dry_run_request()
    prerequest = "\n".join(
        line
        for event in item.get("event", [])
        if event.get("listen") == "prerequest"
        for line in event["script"]["exec"]
    )
    tests = "\n".join(
        line
        for event in item.get("event", [])
        if event.get("listen") == "test"
        for line in event["script"]["exec"]
    )

    assert 'collectionVariables.get("configurationSnapshotRevision")' in prerequest
    assert 'collectionVariables.get("configurationSnapshotConfiguration")' in prerequest
    assert "Run Export Configuration Snapshot" in prerequest
    assert 'collectionVariables.set("configurationCurrentRevision"' in tests
    assert "dryRun.current_revision" in tests
