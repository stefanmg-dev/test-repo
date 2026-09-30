from api import app


SUMMARY_PATHS = {
    "/api/v1/processing-runs/extraction-quality": (
        "Analyze reviewed extraction quality",
        "ExtractionQualityAnalysisModel",
    ),
    "/api/v1/processing-runs/invoice-shadow-summary": (
        "Summarize Universal Invoice shadow validation",
        "InvoiceShadowSummaryModel",
    ),
    "/api/v1/processing-runs/review-summary": (
        "Summarize processing run reviews",
        "ProcessingRunReviewSummaryModel",
    ),
}


def test_processing_summary_operations_are_documented():
    schema = app.openapi()
    for path, (summary, _) in SUMMARY_PATHS.items():
        operation = schema["paths"][path]["get"]
        assert operation["summary"] == summary
        assert "processing-runs:read" in operation["description"]
        assert "tenant-owned" in operation["description"]
        assert operation["responses"]["200"]["description"]


def test_processing_summary_models_are_documented():
    schemas = app.openapi()["components"]["schemas"]
    names = {
        "ExtractionQualityFieldCorrectionModel",
        "ExtractionQualityFieldCountsModel",
        "ExtractionQualityGroupModel",
        "ExtractionQualityAnalysisModel",
        "InvoiceShadowSchemaVersionSummaryModel",
        "InvoiceShadowFailureReasonSummaryModel",
        "InvoiceShadowSummaryModel",
        "ProcessingRunReviewSummaryModel",
    }
    for name in names:
        for field_name, field in schemas[name]["properties"].items():
            assert field.get("description"), f"{name}.{field_name}"


def test_processing_summary_examples_are_synthetic():
    schemas = app.openapi()["components"]["schemas"]
    group = schemas["ExtractionQualityGroupModel"]["properties"]
    assert group["configuration_hash"]["examples"] == ["hash-synthetic"]
    field = schemas["ExtractionQualityFieldCorrectionModel"]["properties"]
    assert field["field_name"]["examples"] == ["invoice_number"]
