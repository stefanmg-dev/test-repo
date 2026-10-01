from api import app


COLLECTION_PATH = (
    "/api/v1/config/document-types/{document_type}/profiles/"
    "{profile_name}/collections/{collection_name}"
)
FIELD_PATH = COLLECTION_PATH + "/fields"
FIELD_ITEM_PATH = FIELD_PATH + "/{field_name}"


def test_profile_collection_operations_are_documented():
    schema = app.openapi()
    operations = {
        (COLLECTION_PATH, "post"): "Add a profile collection",
        (COLLECTION_PATH, "put"): "Replace a profile collection",
        (COLLECTION_PATH, "delete"): "Delete a profile collection",
        (FIELD_PATH, "post"): "Add a profile collection field",
        (FIELD_ITEM_PATH, "put"): "Replace a profile collection field",
        (FIELD_ITEM_PATH, "delete"): "Delete a profile collection field",
    }

    for (path, method), summary in operations.items():
        operation = schema["paths"][path][method]
        assert operation["summary"] == summary
        assert "config:write" in operation["description"]
        status_code = "201" if method == "post" else "200"
        assert operation["responses"][status_code]["description"]


def test_profile_collection_path_parameters_are_documented():
    schema = app.openapi()
    for path, method in (
        (COLLECTION_PATH, "post"),
        (COLLECTION_PATH, "put"),
        (COLLECTION_PATH, "delete"),
        (FIELD_PATH, "post"),
        (FIELD_ITEM_PATH, "put"),
        (FIELD_ITEM_PATH, "delete"),
    ):
        for parameter in schema["paths"][path][method]["parameters"]:
            assert parameter.get("description"), parameter["name"]
