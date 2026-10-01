from api import app


COLLECTION_PATH = (
    "/api/v1/config/document-types/{document_type}/"
    "collections/{collection_name}"
)
FIELD_PATH = COLLECTION_PATH + "/fields"
FIELD_ITEM_PATH = FIELD_PATH + "/{field_name}"


def test_document_collection_operations_are_documented():
    schema = app.openapi()
    operations = {
        (COLLECTION_PATH, "post"): "Add a document collection",
        (COLLECTION_PATH, "put"): "Replace a document collection",
        (COLLECTION_PATH, "delete"): "Delete a document collection",
        (FIELD_PATH, "post"): "Add a document collection field",
        (FIELD_ITEM_PATH, "put"): "Replace a document collection field",
        (FIELD_ITEM_PATH, "delete"): "Delete a document collection field",
    }
    for (path, method), summary in operations.items():
        operation = schema["paths"][path][method]
        assert operation["summary"] == summary
        assert "config:write" in operation["description"]
        for parameter in operation.get("parameters", []):
            assert parameter.get("description"), parameter["name"]


def test_document_collection_models_are_documented():
    schemas = app.openapi()["components"]["schemas"]
    for name in (
        "CollectionItemValidationModel",
        "DocumentCollectionModel",
        "AddCollectionRequest",
        "UpdateCollectionRequest",
    ):
        for field_name, field in schemas[name]["properties"].items():
            assert field.get("description"), f"{name}.{field_name}"


def test_document_collection_examples_are_synthetic():
    schemas = app.openapi()["components"]["schemas"]
    validation = schemas["CollectionItemValidationModel"]["properties"]
    assert validation["message"]["examples"] == [
        "Synthetic reading difference is invalid"
    ]
