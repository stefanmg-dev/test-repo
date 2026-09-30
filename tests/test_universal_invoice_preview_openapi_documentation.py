from api import app


MODELS = {
    "UniversalInvoiceModel",
    "InvoiceServiceModel",
    "InvoiceMeteringPointModel",
    "InvoiceMeterModel",
    "InvoiceConsumptionItemModel",
}


def test_universal_invoice_preview_operation_is_documented():
    operation = app.openapi()["paths"][
        "/api/v1/processing-runs/{run_id}/universal-invoice"
    ]["get"]

    assert operation["summary"] == "Get Universal Invoice preview"
    assert "tenant-owned" in operation["description"]
    assert "processing-runs:read" in operation["description"]
    assert "read-only" in operation["description"]
    assert "Nullable scalar fields" in operation["description"]
    assert operation["parameters"][0]["description"]
    assert "404" in operation["responses"]
    assert "409" in operation["responses"]


def test_universal_invoice_models_are_documented():
    schemas = app.openapi()["components"]["schemas"]
    for name in MODELS:
        for field_name, field in schemas[name]["properties"].items():
            assert field.get("description"), f"{name}.{field_name}"


def test_universal_invoice_examples_are_synthetic():
    schemas = app.openapi()["components"]["schemas"]
    invoice = schemas["UniversalInvoiceModel"]["properties"]
    assert invoice["invoice_number"]["examples"] == ["INV-SYNTH-001"]
    assert invoice["supplier_name"]["examples"] == ["Synthetic Supplier"]
    meter = schemas["InvoiceMeterModel"]["properties"]
    assert meter["meter_number"]["examples"] == ["METER-SYNTH-001"]
