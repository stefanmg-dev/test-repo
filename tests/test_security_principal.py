from security_principal import SecurityPrincipal


def test_principal_checks_explicit_and_admin_scopes():
    reader = SecurityPrincipal(
        principal_type="user",
        subject="user-1",
        tenant_id="tenant-1",
        scopes=frozenset({"processing-runs:read"}),
    )
    admin = SecurityPrincipal(
        principal_type="user",
        subject="admin-1",
        tenant_id="tenant-1",
        scopes=frozenset({"admin"}),
    )

    assert reader.has_scope("processing-runs:read") is True
    assert reader.has_scope("config:write") is False
    assert admin.has_scope("config:write") is True
