from api import app


PATH = "/api/v1/config/document-types/{document_type}/default-profile"


def test_default_profile_operation_is_documented():
    operation = app.openapi()["paths"][PATH]["put"]
    assert operation["summary"] == "Set the default document profile"
    assert "config:write" in operation["description"]
    assert "preserved" in operation["description"]
    assert "Legacy document types are rejected" in operation["description"]


def test_default_profile_parameter_and_request_are_documented():
    operation = app.openapi()["paths"][PATH]["put"]
    parameters = {item["name"]: item for item in operation["parameters"]}
    assert parameters["document_type"]["description"]

    schema = app.openapi()["components"]["schemas"][
        "UpdateDefaultProfileRequest"
    ]
    field = schema["properties"]["profile_name"]
    assert field["description"]
    assert field["minLength"] == 1
    assert field["maxLength"] == 100
    assert field["pattern"] == "^[a-z][a-z0-9_]*$"
