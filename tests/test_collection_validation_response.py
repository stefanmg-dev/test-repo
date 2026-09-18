from extraction_models import ExtractionResponseModel


def response_payload() -> dict:
    return {
        "document_type": "invoice",
        "processing_status": "accepted",
        "profile": "electricity_electrohold",
        "quality": {
            "status": "accepted",
            "requires_review": False,
            "input": {
                "format": "PDF",
                "source": "native_pdf",
                "page_count": 1,
            },
            "warnings": [],
        },
        "raw_text": "sample",
        "llm_values": {},
        "final_values": {},
        "collections": {},
        "validation": {
            "valid": True,
            "errors": {},
        },
    }


def test_response_accepts_collection_validation():
    payload = response_payload()
    payload["collection_validation"] = {
        "valid": False,
        "errors": {
            "meters[0].meter_number": [
                "Meter number is invalid"
            ]
        },
    }

    model = ExtractionResponseModel.model_validate(
        payload
    )

    assert (
        model.collection_validation.model_dump()
        == payload["collection_validation"]
    )


def test_response_defaults_collection_validation_to_valid():
    model = ExtractionResponseModel.model_validate(
        response_payload()
    )

    assert model.collection_validation.model_dump() == {
        "valid": True,
        "errors": {},
    }
