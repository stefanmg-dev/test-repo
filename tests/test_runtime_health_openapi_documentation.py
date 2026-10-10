from api import app


def test_runtime_operations_and_responses_are_documented():
    schema = app.openapi()

    for path in ("/health", "/ready"):
        operation = schema["paths"][path]["get"]
        assert operation["description"]
        assert operation["responses"]["200"]["description"]
        assert (
            operation["responses"]["200"]["content"]
            ["application/json"]["schema"]["$ref"]
        )

    ready_error = schema["paths"]["/ready"]["get"]["responses"]["503"]
    assert ready_error["description"]
    assert ready_error["content"]["application/json"]["schema"]["$ref"]


def test_runtime_response_fields_have_descriptions_and_examples():
    schemas = app.openapi()["components"]["schemas"]

    for name in (
        "HealthResponseModel",
        "ReadinessResponseModel",
        "ReadinessErrorResponseModel",
    ):
        for field_name, field in schemas[name]["properties"].items():
            assert field["description"], f"{name}.{field_name}"
            assert field["examples"], f"{name}.{field_name}"
