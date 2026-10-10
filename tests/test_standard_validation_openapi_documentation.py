from api import app


def test_standard_validation_error_fields_are_documented():
    schemas = app.openapi()["components"]["schemas"]

    http_validation = schemas["HTTPValidationError"]
    detail = http_validation["properties"]["detail"]
    assert detail["description"]
    assert detail["examples"]

    validation_error = schemas["ValidationError"]
    for name in ("loc", "msg", "type", "input", "ctx"):
        field = validation_error["properties"][name]
        assert field["description"], name
        assert field["examples"], name


def test_standard_validation_documentation_is_global_and_cached():
    first = app.openapi()
    second = app.openapi()

    assert first is second

    references = 0
    for operations in first["paths"].values():
        for method in ("get", "post", "put", "delete", "patch"):
            operation = operations.get(method)
            if operation is None:
                continue
            schema = (
                operation.get("responses", {})
                .get("422", {})
                .get("content", {})
                .get("application/json", {})
                .get("schema", {})
            )
            if schema.get("$ref", "").endswith(
                "/HTTPValidationError"
            ):
                references += 1

    assert references > 0
