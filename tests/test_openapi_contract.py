from api import app


def response_schema(responses, status_code):
    return responses[status_code]["content"][
        "application/json"
    ]["schema"]


def test_extract_document_error_responses_are_documented():
    openapi = app.openapi()
    responses = openapi["paths"]["/extract-document"][
        "post"
    ]["responses"]

    assert responses["404"]["description"] == (
        "Document type was not found"
    )
    assert response_schema(responses, "404") == {
        "$ref": "#/components/schemas/ApiErrorResponseModel"
    }

    assert responses["409"]["description"] == (
        "Document type is not ready for extraction"
    )
    assert response_schema(responses, "409") == {
        "$ref": "#/components/schemas/ApiErrorResponseModel"
    }

    assert responses["415"]["description"] == (
        "Unsupported file type"
    )
    assert response_schema(responses, "415") == {
        "$ref": (
            "#/components/schemas/"
            "DocumentInputErrorResponseModel"
        )
    }

    assert responses["422"]["description"] == (
        "Request validation error or invalid document content"
    )
    invalid_document_schema = response_schema(
        responses,
        "422",
    )
    refs = {
        item["$ref"]
        for item in invalid_document_schema["anyOf"]
    }
    assert refs == {
        (
            "#/components/schemas/"
            "RequestValidationErrorResponseModel"
        ),
        (
            "#/components/schemas/"
            "DocumentInputErrorResponseModel"
        ),
    }
