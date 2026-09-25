from collections.abc import Iterable


OIDC_SCOPE_MAPPING = {
    "documents.extract": "documents:extract",
    "processing-runs.read": "processing-runs:read",
    "config.read": "config:read",
    "config.write": "config:write",
    "documents:extract": "documents:extract",
    "processing-runs:read": "processing-runs:read",
    "config:read": "config:read",
    "config:write": "config:write",
}


def normalize_oidc_scopes(scopes: Iterable[str]):
    normalized = set()

    for scope in scopes:
        mapped_scope = OIDC_SCOPE_MAPPING.get(scope)
        if mapped_scope is not None:
            normalized.add(mapped_scope)

    return frozenset(normalized)
