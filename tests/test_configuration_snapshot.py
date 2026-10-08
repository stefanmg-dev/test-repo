import copy

import pytest

from configuration_revision import configuration_revision
from configuration_snapshot import (
    CONFIGURATION_SNAPSHOT_SCHEMA_VERSION,
    ConfigurationSnapshotError,
    build_configuration_snapshot,
    validate_configuration_snapshot,
)
from config_validator import ConfigValidationError


CONFIG = {
    "invoice": {
        "fields": [],
    }
}


def test_snapshot_has_version_revision_and_detached_configuration():
    source = copy.deepcopy(CONFIG)

    snapshot = build_configuration_snapshot(source)

    assert snapshot == {
        "schema_version": CONFIGURATION_SNAPSHOT_SCHEMA_VERSION,
        "revision": configuration_revision(CONFIG),
        "configuration": CONFIG,
    }

    source["invoice"]["fields"].append(
        {
            "name": "supplier_name",
            "type": "constant",
            "value": "synthetic",
        }
    )
    assert snapshot["configuration"] == CONFIG


def test_valid_snapshot_returns_detached_configuration():
    snapshot = build_configuration_snapshot(CONFIG)

    restored = validate_configuration_snapshot(snapshot)

    assert restored == CONFIG
    assert restored is not snapshot["configuration"]


def test_snapshot_rejects_unsupported_schema_version():
    snapshot = build_configuration_snapshot(CONFIG)
    snapshot["schema_version"] = "999"

    with pytest.raises(
        ConfigurationSnapshotError,
        match="Unsupported configuration snapshot schema version",
    ):
        validate_configuration_snapshot(snapshot)


def test_snapshot_rejects_missing_configuration_object():
    snapshot = build_configuration_snapshot(CONFIG)
    snapshot["configuration"] = None

    with pytest.raises(
        ConfigurationSnapshotError,
        match="must contain a configuration object",
    ):
        validate_configuration_snapshot(snapshot)


def test_snapshot_rejects_revision_mismatch():
    snapshot = build_configuration_snapshot(CONFIG)
    snapshot["revision"] = "0" * 64

    with pytest.raises(
        ConfigurationSnapshotError,
        match="revision does not match its content",
    ):
        validate_configuration_snapshot(snapshot)


def test_snapshot_rejects_invalid_configuration():
    with pytest.raises(ConfigValidationError):
        build_configuration_snapshot({})
