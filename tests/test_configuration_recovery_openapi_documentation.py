from api import app


TARGETS = (
    ("get", "/api/v1/config/snapshot"),
    ("post", "/api/v1/config/restore/dry-run"),
    ("post", "/api/v1/config/restore"),
)


def resolve(schema, candidate):
    reference = candidate.get("$ref") if isinstance(candidate, dict) else None
    if not reference:
        return candidate
    name = reference.rsplit("/", 1)[-1]
    return schema["components"]["schemas"][name]


def assert_described_properties(schema, candidate):
    candidate = resolve(schema, candidate)
    for name, field in candidate.get("properties", {}).items():
        description = field.get("description")
        resolved_field = resolve(schema, field)
        assert description or resolved_field.get("description"), name


def test_configuration_recovery_openapi_describes_fields_and_examples():
    schema = app.openapi()

    for method, path in TARGETS:
        operation = schema["paths"][path][method]
        assert operation["description"]
        for parameter in operation.get("parameters", []):
            assert parameter["description"]

        request_schema = (
            operation.get("requestBody", {})
            .get("content", {})
            .get("application/json", {})
            .get("schema", {})
        )
        assert_described_properties(schema, request_schema)

        for response in operation["responses"].values():
            assert response["description"]
            response_schema = (
                response.get("content", {})
                .get("application/json", {})
                .get("schema", {})
            )
            assert_described_properties(schema, response_schema)

    restore_schema = schema["components"]["schemas"][
        "ConfigurationRestoreResponse"
    ]
    assert all(
        field.get("examples")
        for field in restore_schema["properties"].values()
    )


def test_configuration_recovery_openapi_documents_error_details():
    schema = app.openapi()
    error_schema = schema["components"]["schemas"][
        "ConfigurationRecoveryErrorResponse"
    ]
    assert error_schema["properties"]["detail"]["description"]
    assert error_schema["properties"]["detail"]["examples"]

def test_configuration_restore_dry_run_response_fields_have_examples():
    schema = app.openapi()
    response_schema = schema["components"]["schemas"][
        "ConfigurationRestoreDryRunResponse"
    ]

    for name, field in response_schema["properties"].items():
        assert field.get("description"), name
        assert field.get("examples"), name
