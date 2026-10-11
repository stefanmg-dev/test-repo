from pathlib import Path


REFERENCE = Path("docs/api-reference.md")


def test_api_keys_and_auth_reference_documents_public_contracts():
    content = REFERENCE.read_text(encoding="utf-8")
    for heading in (
        '### GET `/api/v1/api-keys`',
        '### POST `/api/v1/api-keys`',
        '### DELETE `/api/v1/api-keys/{api_key_id}`',
        '### POST `/api/v1/api-keys/{api_key_id}/rotate`',
        '### GET `/api/v1/auth/config`',
    ):
        assert heading in content
    assert "returned only in this response" in content
    assert "without exposing confidential credentials" in content
    assert "timezone-aware `expires_at`" in content
