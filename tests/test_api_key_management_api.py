from datetime import datetime, timezone
from types import SimpleNamespace
from uuid import uuid4

from fastapi.testclient import TestClient

from api import app
from security_dependencies import get_api_key_service, get_optional_principal
from security_principal import SecurityPrincipal


class Service:
    def __init__(self):
        self.key = SimpleNamespace(
            id=uuid4(), name="integration", tenant_id="tenant-a",
            secret_prefix="abc", scopes=["documents:extract"],
            created_at=datetime.now(timezone.utc), expires_at=None,
            last_used_at=None, revoked_at=None,
        )

    def create_key(self, **kwargs):
        return SimpleNamespace(api_key=self.key, secret="dpk_abc_secret")

    def list_keys(self, **kwargs):
        return [self.key]

    def rotate_key(self, *args, **kwargs):
        return SimpleNamespace(api_key=self.key, secret="dpk_abc_new")

    def revoke_key(self, *args, **kwargs):
        return self.key


def install(scopes):
    principal = SecurityPrincipal(
        principal_type="user", subject="admin", tenant_id="tenant-a",
        scopes=frozenset(scopes),
    )
    app.dependency_overrides[get_optional_principal] = lambda: principal
    app.dependency_overrides[get_api_key_service] = lambda: Service()


def test_admin_can_create_list_rotate_and_revoke_api_keys():
    install({"admin"})
    client = TestClient(app)
    created = client.post("/api/v1/api-keys", json={
        "name": "integration", "scopes": ["documents:extract"]
    })
    assert created.status_code == 201
    assert created.json()["secret"] == "dpk_abc_secret"
    key_id = created.json()["id"]
    listing = client.get("/api/v1/api-keys")
    assert listing.status_code == 200
    assert "secret" not in listing.json()["items"][0]
    assert client.post(f"/api/v1/api-keys/{key_id}/rotate", json={}).status_code == 200
    assert client.delete(f"/api/v1/api-keys/{key_id}").status_code == 204


def test_non_admin_is_forbidden():
    install({"config:write"})
    assert TestClient(app).get("/api/v1/api-keys").status_code == 403
