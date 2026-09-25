from oidc_scope_mapping import normalize_oidc_scopes


def test_maps_entra_delegated_scopes():
    assert normalize_oidc_scopes(
        {
            "documents.extract",
            "processing-runs.read",
            "config.read",
            "config.write",
        }
    ) == frozenset(
        {
            "documents:extract",
            "processing-runs:read",
            "config:read",
            "config:write",
        }
    )


def test_unknown_and_admin_scopes_are_ignored():
    assert normalize_oidc_scopes(
        {
            "documents.extract",
            "unknown.permission",
            "admin",
        }
    ) == frozenset({"documents:extract"})
