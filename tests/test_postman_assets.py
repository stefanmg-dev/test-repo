import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
POSTMAN = ROOT / "postman"
COLLECTION = POSTMAN / "Document_Processing_API_Stable.postman_collection.json"
ENVIRONMENT = POSTMAN / "Document_Processing_Local.postman_environment.json"


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def requests(items):
    for item in items:
        if "request" in item:
            yield item
        yield from requests(item.get("item", []))


def test_postman_collection_contract_and_safety():
    data = load(COLLECTION)
    assert data["info"]["schema"].endswith("v2.1.0/collection.json")
    assert data["info"]["name"] == "Document Processing API - Stable"
    assert {item["name"] for item in data["item"]} == {
        "00 Health", "01 Extract Document", "02 Processing History",
        "03 Error Contracts", "04 Configuration - Read Only",
        "05 Configuration Recovery",
    }
    names = {item["name"] for item in requests(data["item"])}
    assert {"Health Check", "Readiness Check", "A1 Invoice",
            "Electrohold Invoice",
            "Toplofikacia Invoice", "Generic Fallback",
            "Get Processing Run by ID", "Corrupted PDF - 422"} <= names
    serialized = json.dumps(data, ensure_ascii=False)
    for forbidden in ("/Users/", "DATABASE_URL", "postgresql+psycopg://",
                      "Factura_A1_0826", "Стефан Момчилов"):
        assert forbidden not in serialized


def test_postman_environment_contract_and_safety():
    data = load(ENVIRONMENT)
    values = {item["key"]: item["value"] for item in data["values"]}
    assert values["base_url"] == "http://127.0.0.1:8000"
    assert values["toplofikacia_expected_profile"] == "heating_toplofikacia_sofia"
    assert all(value == "" for key, value in values.items() if key.endswith("_path"))
    serialized = json.dumps(data, ensure_ascii=False)
    assert "/Users/" not in serialized
    assert "DATABASE_URL" not in serialized

def test_postman_configuration_revision_contract():
    data = load(COLLECTION)
    request = next(
        item
        for item in requests(data["item"])
        if item["name"] == "List Document Types"
    )
    script = "\n".join(request["event"][0]["script"]["exec"])

    assert "body.revision" in script
    assert "^[0-9a-f]{64}$" in script
    assert 'headers.get("ETag")' in script
    assert '`"${body.revision}"`' in script


def test_destructive_postman_requests_are_disabled_by_default():
    collection = json.loads(COLLECTION.read_text(encoding="utf-8"))
    environment = json.loads(ENVIRONMENT.read_text(encoding="utf-8"))

    variables = {
        item["key"]: item.get("value")
        for item in environment["values"]
    }
    assert variables["allow_retention_execute"] == "false"
    assert variables["allow_configuration_restore"] == "false"

    def find_request(items, name):
        for item in items:
            if item.get("name") == name and "request" in item:
                return item
            found = find_request(item.get("item", []), name)
            if found is not None:
                return found
        return None

    expected = {
        "Retention Execute": "allow_retention_execute",
        "Apply Guarded Configuration Restore": (
            "allow_configuration_restore"
        ),
    }
    for name, variable in expected.items():
        request = find_request(collection["item"], name)
        assert request is not None
        scripts = [
            line
            for event in request.get("event", [])
            if event.get("listen") == "prerequest"
            for line in event["script"]["exec"]
        ]
        script = "\n".join(scripts)
        assert variable in script
        assert '!== "true"' in script


def test_postman_request_urls_use_defined_base_url_variable():
    collection = load(COLLECTION)
    environment = load(ENVIRONMENT)
    environment_keys = {
        item["key"] for item in environment["values"]
    }

    assert "base_url" in environment_keys

    for item in requests(collection["item"]):
        url = item["request"].get("url", "")
        if isinstance(url, dict):
            url = url.get("raw", "")
        assert "{{baseUrl}}" not in url
        assert url.startswith("{{base_url}}")


def test_postman_configuration_recovery_variables_are_declared():
    collection = load(COLLECTION)
    variables = {
        item["key"]: item.get("value")
        for item in collection.get("variable", [])
    }

    assert variables["configurationSnapshotRevision"] == ""
    assert variables["configurationSnapshotConfiguration"] == ""
    assert variables["configurationCurrentRevision"] == ""
