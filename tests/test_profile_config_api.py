from copy import deepcopy

from fastapi.testclient import TestClient

import routes_config_v1
from api import app


INITIAL_CONFIG = {
    "invoice": {
        "default_profile": "telecom_a1",
        "common_fields": [
            {
                "name": "invoice_number",
                "type": "regex",
                "rule": "([0-9]+)",
                "validation": [],
            }
        ],
        "profiles": {
            "telecom_a1": {
                "fields": [
                    {
                        "name": "contract_number",
                        "type": "regex",
                        "rule": "([МM][0-9]+)",
                        "validation": [],
                    }
                ]
            }
        },
    }
}


def configure_in_memory_store(
    monkeypatch,
):
    state = {
        "config": deepcopy(INITIAL_CONFIG)
    }

    def fake_load_config():
        return deepcopy(state["config"])

    def fake_save_validated_config(config):
        state["config"] = deepcopy(config)

    monkeypatch.setattr(
        routes_config_v1,
        "load_config",
        fake_load_config,
    )

    monkeypatch.setattr(
        routes_config_v1,
        "save_validated_config",
        fake_save_validated_config,
    )

    return state


def test_adds_common_field(
    monkeypatch,
):
    state = configure_in_memory_store(
        monkeypatch
    )

    client = TestClient(app)

    response = client.post(
        "/api/v1/config/document-types/"
        "invoice/common-fields",
        json={
            "field": {
                "name": "total_amount",
                "type": "regex",
                "rule": "([0-9]+\\.[0-9]+)",
                "validation": [],
            }
        },
    )

    assert response.status_code == 201

    common_fields = state["config"][
        "invoice"
    ][
        "common_fields"
    ]

    assert [
        field["name"]
        for field in common_fields
    ] == [
        "invoice_number",
        "total_amount",
    ]


def test_updates_common_field(
    monkeypatch,
):
    state = configure_in_memory_store(
        monkeypatch
    )

    client = TestClient(app)

    response = client.put(
        "/api/v1/config/document-types/"
        "invoice/common-fields/"
        "invoice_number",
        json={
            "field": {
                "name": "invoice_number",
                "type": "regex",
                "rule": "Фактура\\s*([0-9]+)",
                "validation": [],
            }
        },
    )

    assert response.status_code == 200

    updated_field = state["config"][
        "invoice"
    ][
        "common_fields"
    ][0]

    assert updated_field["rule"] == (
        "Фактура\\s*([0-9]+)"
    )


def test_deletes_common_field(
    monkeypatch,
):
    state = configure_in_memory_store(
        monkeypatch
    )

    client = TestClient(app)

    response = client.delete(
        "/api/v1/config/document-types/"
        "invoice/common-fields/"
        "invoice_number"
    )

    assert response.status_code == 200

    assert state["config"][
        "invoice"
    ][
        "common_fields"
    ] == []


def test_adds_profile_field(
    monkeypatch,
):
    state = configure_in_memory_store(
        monkeypatch
    )

    client = TestClient(app)

    response = client.post(
        "/api/v1/config/document-types/"
        "invoice/profiles/"
        "telecom_a1/fields",
        json={
            "field": {
                "name": "customer_number",
                "type": "regex",
                "rule": "Клиент\\s*([0-9]+)",
                "validation": [],
            }
        },
    )

    assert response.status_code == 201

    profile_fields = state["config"][
        "invoice"
    ][
        "profiles"
    ][
        "telecom_a1"
    ][
        "fields"
    ]

    assert [
        field["name"]
        for field in profile_fields
    ] == [
        "contract_number",
        "customer_number",
    ]


def test_updates_profile_field(
    monkeypatch,
):
    state = configure_in_memory_store(
        monkeypatch
    )

    client = TestClient(app)

    response = client.put(
        "/api/v1/config/document-types/"
        "invoice/profiles/"
        "telecom_a1/fields/"
        "contract_number",
        json={
            "field": {
                "name": "contract_number",
                "type": "regex",
                "rule": (
                    "Договор\\s*"
                    "([МM][0-9]+)"
                ),
                "validation": [],
            }
        },
    )

    assert response.status_code == 200

    updated_field = state["config"][
        "invoice"
    ][
        "profiles"
    ][
        "telecom_a1"
    ][
        "fields"
    ][0]

    assert updated_field["rule"] == (
        "Договор\\s*([МM][0-9]+)"
    )


def test_deletes_profile_field(
    monkeypatch,
):
    state = configure_in_memory_store(
        monkeypatch
    )

    client = TestClient(app)

    response = client.delete(
        "/api/v1/config/document-types/"
        "invoice/profiles/"
        "telecom_a1/fields/"
        "contract_number"
    )

    assert response.status_code == 200

    assert state["config"][
        "invoice"
    ][
        "profiles"
    ][
        "telecom_a1"
    ][
        "fields"
    ] == []


def test_rejects_duplicate_between_common_and_profile(
    monkeypatch,
):
    configure_in_memory_store(
        monkeypatch
    )

    client = TestClient(app)

    response = client.post(
        "/api/v1/config/document-types/"
        "invoice/profiles/"
        "telecom_a1/fields",
        json={
            "field": {
                "name": "invoice_number",
                "type": "regex",
                "rule": "([0-9]+)",
                "validation": [],
            }
        },
    )

    assert response.status_code == 409

    assert "already exists" in (
        response.json()["detail"]
    )


def test_unknown_profile_returns_404(
    monkeypatch,
):
    configure_in_memory_store(
        monkeypatch
    )

    client = TestClient(app)

    response = client.post(
        "/api/v1/config/document-types/"
        "invoice/profiles/"
        "unknown_profile/fields",
        json={
            "field": {
                "name": "customer_number",
                "type": "regex",
                "rule": "([0-9]+)",
                "validation": [],
            }
        },
    )

    assert response.status_code == 404

    assert "unknown_profile" in (
        response.json()["detail"]
    )