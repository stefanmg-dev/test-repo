import json
from pathlib import Path


COLLECTION = Path(
    "postman/Document_Processing_API_Stable.postman_collection.json"
)


def get_restore_request():
    collection = json.loads(COLLECTION.read_text(encoding="utf-8"))
    folder = next(
        item
        for item in collection["item"]
        if item["name"] == "05 Configuration Recovery"
    )
    return next(
        item
        for item in folder["item"]
        if item["name"] == "Apply Guarded Configuration Restore"
    )


def test_postman_contains_guarded_restore_request():
    item = get_restore_request()

    assert item["request"]["method"] == "POST"
    assert item["request"]["url"]["raw"] == (
        "{{baseUrl}}/api/v1/config/restore"
    )
    assert item["request"]["url"]["path"] == [
        "api", "v1", "config", "restore"
    ]
    assert "config:write" in item["request"]["description"]


def test_postman_guarded_restore_has_safety_inputs_and_checks():
    item = get_restore_request()
    raw = item["request"]["body"]["raw"]
    script = "\n".join(item["event"][0]["script"]["exec"])

    assert "configurationSnapshotRevision" in raw
    assert "configurationSnapshotConfiguration" in raw
    assert "configurationCurrentRevision" in raw
    assert '"confirmation": "RESTORE"' in raw
    assert "body.restore_applied" in script
    assert "body.backup_identifier" in script
    assert "body.configuration_write" in script
