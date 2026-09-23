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
    }
    names = {item["name"] for item in requests(data["item"])}
    assert {"Health Check", "A1 Invoice", "Electrohold Invoice",
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
