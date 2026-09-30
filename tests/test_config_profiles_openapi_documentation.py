from api import app


PATH = "/api/v1/config/document-types/{document_type}/profiles/{profile_name}"


def test_profile_operations_are_documented():
    operations = app.openapi()["paths"][PATH]

    assert operations["post"]["summary"] == (
        "Add a document configuration profile"
    )
    assert "config:write" in operations["post"]["description"]
    assert "Legacy document types are rejected" in (
        operations["post"]["description"]
    )
    assert operations["delete"]["summary"] == (
        "Delete a document configuration profile"
    )
    assert "config:write" in operations["delete"]["description"]
    assert "non-default profile" in operations["delete"]["description"]


def test_profile_path_parameters_are_documented():
    operations = app.openapi()["paths"][PATH]
    for method in ("post", "delete"):
        parameters = {
            item["name"]: item
            for item in operations[method]["parameters"]
        }
        assert parameters["document_type"]["description"]
        assert parameters["profile_name"]["description"]
        schema = parameters["profile_name"]["schema"]
        assert schema["minLength"] == 1
        assert schema["maxLength"] == 100
        assert schema["pattern"] == "^[a-z][a-z0-9_]*$"


def test_profile_models_are_documented():
    schemas = app.openapi()["components"]["schemas"]
    for name in ("DocumentProfileModel", "AddProfileRequest"):
        for field_name, field in schemas[name]["properties"].items():
            assert field.get("description"), f"{name}.{field_name}"
