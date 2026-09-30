from api import app


CORE_OPERATIONS = {
    ("/api/v1/config/document-types", "get"): (
        "List document type configurations",
        "config:read",
    ),
    ("/api/v1/config/document-types", "post"): (
        "Create a document type configuration",
        "config:write",
    ),
    ("/api/v1/config/document-types/{document_type}", "get"): (
        "Get a document type configuration",
        "config:read",
    ),
    ("/api/v1/config/document-types/{document_type}", "delete"): (
        "Delete a document type configuration",
        "config:write",
    ),
    ("/api/v1/config/document-types/{document_type}/rename", "put"): (
        "Rename a document type configuration",
        "config:write",
    ),
}


def test_core_document_type_operations_are_documented():
    schema = app.openapi()
    for (path, method), (summary, scope) in CORE_OPERATIONS.items():
        operation = schema["paths"][path][method]
        assert operation["summary"] == summary
        assert scope in operation["description"]


def test_core_document_type_path_parameters_are_documented():
    schema = app.openapi()
    for path, method in (
        ("/api/v1/config/document-types/{document_type}", "get"),
        ("/api/v1/config/document-types/{document_type}", "delete"),
        ("/api/v1/config/document-types/{document_type}/rename", "put"),
    ):
        parameter = schema["paths"][path][method]["parameters"][0]
        assert parameter["name"] == "document_type"
        assert parameter["description"]


def test_core_configuration_models_are_documented():
    schemas = app.openapi()["components"]["schemas"]
    for name in (
        "DocumentTypeMetadataModel",
        "CreateDocumentTypeRequest",
        "RenameDocumentTypeRequest",
        "ResolvedDocumentTypeModel",
        "ConfigResponse",
        "OperationResponse",
    ):
        for field_name, field in schemas[name]["properties"].items():
            assert field.get("description"), f"{name}.{field_name}"


def test_document_type_examples_are_synthetic():
    schemas = app.openapi()["components"]["schemas"]
    create = schemas["CreateDocumentTypeRequest"]["properties"]
    rename = schemas["RenameDocumentTypeRequest"]["properties"]
    assert create["document_type"]["examples"] == ["synthetic_contract"]
    assert rename["new_document_type"]["examples"] == [
        "synthetic_agreement"
    ]
