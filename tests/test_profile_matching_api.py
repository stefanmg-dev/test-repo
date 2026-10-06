from copy import deepcopy

from fastapi.testclient import TestClient

import routes_config_v1
from api import app


INITIAL_CONFIG = {
    "invoice": {
        "default_profile": "synthetic_provider",
        "common_fields": [],
        "profiles": {
            "synthetic_provider": {
                "matching": {
                    "any_of": [
                        {
                            "code": "old_company",
                            "pattern": "old company",
                        }
                    ]
                },
                "fields": [
                    {
                        "name": "account_number",
                        "type": "constant",
                        "value": "FIXED",
                        "validation": [],
                    }
                ],
                "collections": {
                    "items": {
                        "cardinality": "zero_or_more",
                        "fields": [],
                        "item_validations": [],
                    }
                },
                "summary_validations": [],
            }
        },
        "collections": {},
    }
}


def configure_store(monkeypatch, config=None):
    state = {"config": deepcopy(config or INITIAL_CONFIG)}

    monkeypatch.setattr(
        routes_config_v1,
        "load_config",
        lambda: deepcopy(state["config"]),
    )
    monkeypatch.setattr(
        routes_config_v1,
        "save_validated_config",
        lambda value: state.update(config=deepcopy(value)),
    )
    return state


def matching_payload():
    return {
        "matching": {
            "any_of": [
                {
                    "code": "new_company",
                    "pattern": r"\bnew company ead\b",
                },
                {
                    "code": "new_domain",
                    "pattern": r"new\.example",
                },
            ]
        }
    }


def endpoint(profile_name="synthetic_provider"):
    return (
        "/api/v1/config/document-types/invoice/profiles/"
        f"{profile_name}/matching"
    )


def test_replaces_only_profile_matching(monkeypatch):
    state = configure_store(monkeypatch)
    before = deepcopy(
        state["config"]["invoice"]["profiles"]["synthetic_provider"]
    )

    response = TestClient(app).put(endpoint(), json=matching_payload())

    assert response.status_code == 200
    profile = state["config"]["invoice"]["profiles"][
        "synthetic_provider"
    ]
    assert profile["matching"] == matching_payload()["matching"]
    assert profile["fields"] == before["fields"]
    assert profile["collections"] == before["collections"]
    assert profile["summary_validations"] == before["summary_validations"]


def test_unknown_profile_returns_404(monkeypatch):
    configure_store(monkeypatch)
    response = TestClient(app).put(
        endpoint("missing_profile"),
        json=matching_payload(),
    )
    assert response.status_code == 404


def test_legacy_document_type_returns_409(monkeypatch):
    configure_store(monkeypatch, {"invoice": {"fields": []}})
    response = TestClient(app).put(endpoint(), json=matching_payload())
    assert response.status_code == 409


def test_invalid_matching_payloads_return_422(monkeypatch):
    configure_store(monkeypatch)
    invalid_payloads = [
        {"matching": {"any_of": []}},
        {
            "matching": {
                "any_of": [
                    {"code": "Invalid Code", "pattern": "valid"}
                ]
            }
        },
        {
            "matching": {
                "any_of": [
                    {"code": "valid_code", "pattern": "("}
                ]
            }
        },
        {
            "matching": {
                "any_of": [
                    {"code": "duplicate", "pattern": "first"},
                    {"code": "duplicate", "pattern": "second"},
                ]
            }
        },
    ]
    for payload in invalid_payloads:
        response = TestClient(app).put(endpoint(), json=payload)
        assert response.status_code == 422
