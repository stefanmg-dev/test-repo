import hashlib
import json
from copy import deepcopy
from typing import Any


CONFIGURATION_SCHEMA_VERSION = "1"


def build_configuration_snapshot(
    *,
    document_type: str,
    selected_profile: str | None,
    resolved_fields: list[dict[str, Any]],
    resolved_collections: dict[str, Any],
    resolved_summary_validations: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "schema_version": CONFIGURATION_SCHEMA_VERSION,
        "document_type": document_type,
        "selected_profile": selected_profile,
        "resolved_fields": deepcopy(resolved_fields),
        "resolved_collections": deepcopy(
            resolved_collections
        ),
        "resolved_summary_validations": deepcopy(
            resolved_summary_validations
        ),
    }


def canonical_configuration_json(
    snapshot: dict[str, Any],
) -> str:
    return json.dumps(
        snapshot,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )


def configuration_sha256(
    snapshot: dict[str, Any],
) -> str:
    canonical = canonical_configuration_json(snapshot)
    return hashlib.sha256(
        canonical.encode("utf-8")
    ).hexdigest()
