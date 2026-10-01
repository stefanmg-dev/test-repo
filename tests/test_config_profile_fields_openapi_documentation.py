from api import app


ADD_PATH = (
    "/api/v1/config/document-types/{document_type}/"
    "profiles/{profile_name}/fields"
)
ITEM_PATH = ADD_PATH + "/{field_name}"


def test_profile_field_operations_are_documented():
    schema = app.openapi()
    operations = {
        (ADD_PATH, "post"): "Add a profile extraction field",
        (ITEM_PATH, "put"): "Replace a profile extraction field",
        (ITEM_PATH, "delete"): "Delete a profile extraction field",
    }

    for (path, method), summary in operations.items():
        operation = schema["paths"][path][method]
        assert operation["summary"] == summary
        assert "config:write" in operation["description"]
        status_code = "201" if method == "post" else "200"
        assert operation["responses"][status_code]["description"]


def test_profile_field_uniqueness_contract_is_documented():
    schema = app.openapi()
    add_description = schema["paths"][ADD_PATH]["post"]["description"]
    update_description = schema["paths"][ITEM_PATH]["put"]["description"]

    assert "unique across all common and profile fields" in add_description
    assert "unique across the resolved document configuration" in (
        update_description
    )


def test_profile_field_path_parameters_are_documented():
    schema = app.openapi()
    for path, method in (
        (ADD_PATH, "post"),
        (ITEM_PATH, "put"),
        (ITEM_PATH, "delete"),
    ):
        parameters = schema["paths"][path][method]["parameters"]
        for parameter in parameters:
            assert parameter.get("description"), parameter["name"]
