from pathlib import Path


REFERENCE = Path("docs/api-reference.md")


def test_configuration_recovery_manual_reference_documents_contracts():
    content = REFERENCE.read_text(encoding="utf-8")

    for heading in (
        '### GET `/api/v1/config/snapshot`',
        '### POST `/api/v1/config/restore/dry-run`',
        '### POST `/api/v1/config/restore`',
    ):
        assert heading in content

    for field in (
        "schema_version",
        "revision",
        "configuration",
        "snapshot_revision",
        "current_revision",
        "changes_detected",
        "document_types",
        "expected_current_revision",
        "confirmation",
        "restore_applied",
        "previous_revision",
        "restored_revision",
        "backup_revision",
        "backup_identifier",
        "configuration_write",
        "detail",
    ):
        assert f"`{field}`" in content


def test_configuration_recovery_manual_reference_has_examples():
    content = REFERENCE.read_text(encoding="utf-8")

    assert content.count("**Example request:**") >= 2
    assert content.count("**Example response:**") >= 3
    assert "**Example `409` response:**" in content
    assert "**Example `422` response:**" in content
    assert '"confirmation": "RESTORE"' in content
