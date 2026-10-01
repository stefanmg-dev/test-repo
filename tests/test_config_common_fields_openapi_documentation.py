from api import app


ADD_PATH = (
    "/api/v1/config/document-types/{document_type}/common-fields"
)
ITEM_PATH = (
    "/api/v1/config/document-types/{document_type}/"
    "common-fields/{field_name}"
)


def test_common_field_operations_are_documented():
    schema = app.openapi()
    operations = {
        (ADD_PATH, "post"): "Add a common extraction field",
        (ITEM_PATH, "put"): "Replace a common extraction field",
        (ITEM_PATH, "delete"): "Delete a common extraction field",
    }

    for (path, method), summary in operations.items():
        operation = schema["paths"][path][method]
        assert operation["summary"] == summary
        assert "config:write" in operation["description"]
        assert operation["responses"]["200" if method != "post" else "201"][
            "description"
        ]


def test_common_field_uniqueness_contract_is_documented():
    schema = app.openapi()
    add_description = schema["paths"][ADD_PATH]["post"]["description"]
    update_description = schema["paths"][ITEM_PATH]["put"]["description"]

    assert "unique across common and profile fields" in add_description
    assert "unique across the resolved document configuration" in (
        update_description
    )


def test_common_field_path_parameters_are_documented():
    schema = app.openapi()
    for path, method in (
        (ADD_PATH, "post"),
        (ITEM_PATH, "put"),
        (ITEM_PATH, "delete"),
    ):
        for parameter in schema["paths"][path][method]["parameters"]:
            assert parameter.get("description"), parameter["name"]
