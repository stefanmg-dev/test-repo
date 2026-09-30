from api import app


def test_legacy_field_operations_are_documented():
    schema = app.openapi()
    operations = {
        (
            "/api/v1/config/document-types/{document_type}/fields",
            "post",
        ): "Add a legacy extraction field",
        (
            "/api/v1/config/document-types/{document_type}/fields/{field_name}",
            "put",
        ): "Replace a legacy extraction field",
        (
            "/api/v1/config/document-types/{document_type}/fields/{field_name}",
            "delete",
        ): "Delete a legacy extraction field",
    }
    for (path, method), summary in operations.items():
        operation = schema["paths"][path][method]
        assert operation["summary"] == summary
        assert "config:write" in operation["description"]
        for parameter in operation.get("parameters", []):
            assert parameter.get("description"), parameter["name"]


def test_legacy_field_models_are_documented():
    schemas = app.openapi()["components"]["schemas"]
    for name in (
        "ValidationRuleModel",
        "DocumentFieldModel",
        "AddFieldRequest",
        "UpdateFieldRequest",
    ):
        for field_name, field in schemas[name]["properties"].items():
            assert field.get("description"), f"{name}.{field_name}"


def test_legacy_field_examples_are_synthetic():
    schemas = app.openapi()["components"]["schemas"]
    field = schemas["DocumentFieldModel"]["properties"]
    assert field["name"]["examples"] == ["synthetic_invoice_number"]
    validation = schemas["ValidationRuleModel"]["properties"]
    assert validation["message"]["examples"] == [
        "Synthetic invoice number is required"
    ]
