from api import app


DOCUMENTED_SCHEMAS = {
    "DocumentInputErrorResponseModel",
    "ExtractionResponseModel",
    "ExtractionValidationModel",
    "ImageQualityInputModel",
    "InputQualityModel",
    "PdfPageQualityInputModel",
    "PdfQualityInputModel",
    "QualityWarningModel",
    "RequestValidationErrorResponseModel",
    "RequestValidationIssueModel",
}


def test_extract_document_operation_is_self_describing():
    operation = app.openapi()["paths"]["/extract-document"]["post"]

    assert operation["summary"] == (
        "Extract structured data from a document"
    )
    assert "documents:extract" in operation["description"]
    assert "synchronously" in operation["description"]
    assert operation["responses"]["200"]["description"].startswith(
        "Extraction result"
    )


def test_extract_document_multipart_fields_are_documented():
    openapi = app.openapi()
    operation = openapi["paths"]["/extract-document"]["post"]
    request_schema = operation["requestBody"]["content"][
        "multipart/form-data"
    ]["schema"]
    body_name = request_schema["$ref"].rsplit("/", 1)[-1]
    properties = openapi["components"]["schemas"][body_name][
        "properties"
    ]

    assert properties["document_type"]["description"]
    assert properties["document_type"]["examples"] == ["invoice"]
    assert properties["file"]["description"]


def test_extraction_schema_fields_have_descriptions():
    schemas = app.openapi()["components"]["schemas"]

    for schema_name in DOCUMENTED_SCHEMAS:
        for field_name, field in schemas[schema_name].get(
            "properties", {}
        ).items():
            assert field.get("description"), (
                f"{schema_name}.{field_name} lacks description"
            )


def test_extraction_examples_are_synthetic():
    schemas = app.openapi()["components"]["schemas"]
    response = schemas["ExtractionResponseModel"]["properties"]

    assert response["document_type"]["examples"] == ["invoice"]
    assert response["final_values"]["examples"] == [
        {"invoice_number": "INV-SYNTH-001"}
    ]
