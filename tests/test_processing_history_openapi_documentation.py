from api import app


def test_processing_history_operations_are_documented():
    schema = app.openapi()
    listing = schema["paths"]["/api/v1/processing-runs"]["get"]
    detail = schema["paths"]["/api/v1/processing-runs/{run_id}"]["get"]

    assert listing["summary"] == "List processing runs"
    assert "processing-runs:read" in listing["description"]
    assert "AND semantics" in listing["description"]
    assert detail["summary"] == "Get processing run details"
    assert "processing-runs:read" in detail["description"]


def test_processing_history_parameters_are_documented():
    schema = app.openapi()
    operations = [
        schema["paths"]["/api/v1/processing-runs"]["get"],
        schema["paths"]["/api/v1/processing-runs/{run_id}"]["get"],
    ]
    for operation in operations:
        for parameter in operation.get("parameters", []):
            assert parameter.get("description"), parameter["name"]


def test_processing_history_models_are_documented():
    schemas = app.openapi()["components"]["schemas"]
    for name in (
        "ProcessingRunListItemModel",
        "ProcessingRunDetailModel",
        "ProcessingRunListResponseModel",
    ):
        for field_name, field in schemas[name]["properties"].items():
            assert field.get("description"), f"{name}.{field_name}"


def test_processing_history_examples_are_synthetic():
    schemas = app.openapi()["components"]["schemas"]
    item = schemas["ProcessingRunListItemModel"]["properties"]
    assert item["filename"]["examples"] == ["synthetic-invoice.pdf"]
    assert item["id"]["examples"] == [
        "00000000-0000-4000-8000-000000000001"
    ]
