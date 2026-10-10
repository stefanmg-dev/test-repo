import json
from pathlib import Path

COLLECTION = Path(
    "postman/Document_Processing_API_Stable.postman_collection.json"
)


def get_snapshot_request():
    collection = json.loads(COLLECTION.read_text(encoding="utf-8"))
    folder = next(
        item
        for item in collection["item"]
        if item["name"] == "04 Configuration - Read Only"
    )
    return next(
        item
        for item in folder["item"]
        if item["name"] == "Export Configuration Snapshot"
    )


def test_postman_contains_configuration_snapshot_request():
    item = get_snapshot_request()
    assert item["request"]["method"] == "GET"
    assert item["request"]["url"]["raw"] == (
        "{{baseUrl}}/api/v1/config/snapshot"
    )
    assert item["request"]["url"]["path"] == [
        "api", "v1", "config", "snapshot"
    ]
    assert "config:read" in item["request"]["description"]


def test_postman_snapshot_request_checks_response_contract():
    item = get_snapshot_request()
    script = "\n".join(item["event"][0]["script"]["exec"])
    assert "pm.response.to.have.status(200)" in script
    assert "body.schema_version" in script
    assert "body.revision" in script
    assert "body.configuration" in script
