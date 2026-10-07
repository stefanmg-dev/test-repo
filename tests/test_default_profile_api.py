from copy import deepcopy

from fastapi.testclient import TestClient

import routes_config_v1
from api import app


INITIAL_CONFIG = {
    "invoice": {
        "default_profile": "telecom_a1",
        "common_fields": [],
        "profiles": {
            "telecom_a1": {
                "fields": [],
            },
            "synthetic_provider": {
                "matching": {
                    "any_of": [
                        {
                            "code": "synthetic_company",
                            "pattern": "synthetic provider ead",
                        }
                    ]
                },
                "fields": [],
                "collections": {},
                "summary_validations": [],
            },
        },
        "collections": {},
    }
}


def configure_store(monkeypatch, config=None):
    state = {
        "config": deepcopy(config or INITIAL_CONFIG),
        "save_count": 0,
    }

    monkeypatch.setattr(
        routes_config_v1,
        "load_config",
        lambda: deepcopy(state["config"]),
    )

    def save(value):
        state["config"] = deepcopy(value)
        state["save_count"] += 1

    monkeypatch.setattr(routes_config_v1, "save_validated_config", save)
    return state


def endpoint():
    return "/api/v1/config/document-types/invoice/default-profile"


def test_sets_existing_profile_as_default_and_preserves_configuration(
    monkeypatch,
):
    state = configure_store(monkeypatch)
    before = deepcopy(state["config"]["invoice"])

    response = TestClient(app).put(
        endpoint(),
        json={"profile_name": "synthetic_provider"},
    )

    assert response.status_code == 200
    invoice = state["config"]["invoice"]
    assert invoice["default_profile"] == "synthetic_provider"
    assert invoice["common_fields"] == before["common_fields"]
    assert invoice["profiles"] == before["profiles"]
    assert invoice["collections"] == before["collections"]
    assert state["save_count"] == 1


def test_current_default_update_is_idempotent(monkeypatch):
    state = configure_store(monkeypatch)

    response = TestClient(app).put(
        endpoint(),
        json={"profile_name": "telecom_a1"},
    )

    assert response.status_code == 200
    assert response.json()["message"] == (
        "Profile 'telecom_a1' remains the default"
    )
    assert state["save_count"] == 0


def test_unknown_profile_returns_404(monkeypatch):
    configure_store(monkeypatch)
    response = TestClient(app).put(
        endpoint(),
        json={"profile_name": "missing_profile"},
    )
    assert response.status_code == 404


def test_legacy_document_type_returns_409(monkeypatch):
    configure_store(monkeypatch, {"invoice": {"fields": []}})
    response = TestClient(app).put(
        endpoint(),
        json={"profile_name": "telecom_a1"},
    )
    assert response.status_code == 409


def test_invalid_profile_name_returns_422(monkeypatch):
    configure_store(monkeypatch)
    response = TestClient(app).put(
        endpoint(),
        json={"profile_name": "Invalid Profile!"},
    )
    assert response.status_code == 422
