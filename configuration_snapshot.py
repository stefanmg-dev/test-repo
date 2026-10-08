from copy import deepcopy
from typing import Any, Final

from configuration_revision import configuration_revision
from config_validator import validate_config


CONFIGURATION_SNAPSHOT_SCHEMA_VERSION: Final = "1"


class ConfigurationSnapshotError(ValueError):
    pass


def build_configuration_snapshot(config: dict[str, Any]) -> dict[str, Any]:
    validate_config(config)

    return {
        "schema_version": CONFIGURATION_SNAPSHOT_SCHEMA_VERSION,
        "revision": configuration_revision(config),
        "configuration": deepcopy(config),
    }


def validate_configuration_snapshot(
    snapshot: dict[str, Any],
) -> dict[str, Any]:
    if not isinstance(snapshot, dict):
        raise ConfigurationSnapshotError(
            "Configuration snapshot must be an object"
        )

    if snapshot.get("schema_version") != CONFIGURATION_SNAPSHOT_SCHEMA_VERSION:
        raise ConfigurationSnapshotError(
            "Unsupported configuration snapshot schema version"
        )

    configuration = snapshot.get("configuration")
    if not isinstance(configuration, dict):
        raise ConfigurationSnapshotError(
            "Configuration snapshot must contain a configuration object"
        )

    validate_config(configuration)

    expected_revision = configuration_revision(configuration)
    if snapshot.get("revision") != expected_revision:
        raise ConfigurationSnapshotError(
            "Configuration snapshot revision does not match its content"
        )

    return deepcopy(configuration)
