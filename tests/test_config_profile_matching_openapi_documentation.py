from api import app


PATH = (
    "/api/v1/config/document-types/{document_type}/profiles/"
    "{profile_name}/matching"
)


def test_profile_matching_operation_is_documented():
    operation = app.openapi()["paths"][PATH]["put"]
    assert operation["summary"] == "Replace profile supplier matching rules"
    assert "config:write" in operation["description"]
    assert "preserved" in operation["description"]


def test_profile_matching_parameters_are_documented():
    operation = app.openapi()["paths"][PATH]["put"]
    parameters = {item["name"]: item for item in operation["parameters"]}
    assert parameters["document_type"]["description"]
    assert parameters["profile_name"]["description"]
    schema = parameters["profile_name"]["schema"]
    assert schema["pattern"] == "^[a-z][a-z0-9_]*$"


def test_profile_matching_request_model_is_documented():
    schema = app.openapi()["components"]["schemas"][
        "UpdateProfileMatchingRequest"
    ]
    assert schema["properties"]["matching"]["description"]
