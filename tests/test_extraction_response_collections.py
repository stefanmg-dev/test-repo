import pytest
from pydantic import ValidationError
from extraction_models import ExtractionResponseModel


def payload():
    return {
        "document_type": "invoice",
        "processing_status": "accepted",
        "profile": "electricity_electrohold",
        "quality": {
            "status": "accepted",
            "requires_review": False,
            "input": {"format": "PDF", "source": "native_pdf", "page_count": 1},
            "warnings": [],
        },
        "raw_text": "sample",
        "llm_values": {},
        "final_values": {},
        "validation": {"valid": True, "errors": {}},
    }


def test_accepts_typed_collections():
    data = payload()
    data["collections"] = {"meters": [{"meter_number": "1021015029"}], "services": []}
    assert ExtractionResponseModel.model_validate(data).collections == data["collections"]


def test_defaults_collections_to_empty_object():
    assert ExtractionResponseModel.model_validate(payload()).collections == {}


def test_rejects_non_list_collection_value():
    data = payload()
    data["collections"] = {"meters": {"meter_number": "1021015029"}}
    with pytest.raises(ValidationError):
        ExtractionResponseModel.model_validate(data)
