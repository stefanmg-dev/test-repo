from api import app


def test_extract_document_error_responses_are_documented():
    openapi = app.openapi()
    responses = openapi["paths"]["/extract-document"][
        "post"
    ]["responses"]

    unsupported_schema = responses["415"]["content"][
        "application/json"
    ]["schema"]
    assert unsupported_schema == {
        "$ref": (
            "#/components/schemas/"
            "DocumentInputErrorResponseModel"
        )
    }

    invalid_document_response = responses["422"]
    assert invalid_document_response["description"] == (
        "Request validation error or invalid document content"
    )

    invalid_document_schema = invalid_document_response[
        "content"
    ]["application/json"]["schema"]
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
