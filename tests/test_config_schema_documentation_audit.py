from api import app


MODEL_NAMES = (
    "ValidationRuleModel",
    "DocumentFieldModel",
    "CollectionItemValidationModel",
    "DocumentCollectionModel",
    "CollectionSummaryValidationModel",
    "SupplierMatchRuleModel",
    "SupplierMatchingModel",
    "DocumentProfileModel",
    "DocumentTypeModel",
    "DocumentTypeMetadataModel",
    "CreateDocumentTypeRequest",
    "AddProfileRequest",
    "RenameDocumentTypeRequest",
    "AddFieldRequest",
    "UpdateFieldRequest",
    "AddCollectionRequest",
    "UpdateCollectionRequest",
    "ResolvedDocumentTypeModel",
    "ConfigResponse",
    "OperationResponse",
)


def test_all_configuration_operations_are_documented():
    schema = app.openapi()
    for path, path_item in schema["paths"].items():
        if not path.startswith("/api/v1/config/"):
            continue
        for method, operation in path_item.items():
            if method not in {"get", "post", "put", "delete"}:
                continue
            name = f"{method.upper()} {path}"
            assert operation.get("summary"), name
            assert operation.get("description"), name
            for parameter in operation.get("parameters", []):
                assert parameter.get("description"), (
                    f"{name}: {parameter['name']}"
                )


def test_all_configuration_schema_fields_are_documented():
    schemas = app.openapi()["components"]["schemas"]
    for model_name in MODEL_NAMES:
        model = schemas[model_name]
        for field_name, field in model.get("properties", {}).items():
            assert field.get("description"), (
                f"{model_name}.{field_name}"
            )


def test_remaining_configuration_examples_are_synthetic():
    schemas = app.openapi()["components"]["schemas"]
    summary = schemas["CollectionSummaryValidationModel"]["properties"]
    document_type = schemas["DocumentTypeModel"]["properties"]
    assert summary["collection"]["examples"] == ["synthetic_services"]
    assert document_type["default_profile"]["examples"] == [
        "synthetic_provider"
    ]
