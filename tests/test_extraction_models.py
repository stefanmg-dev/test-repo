import pytest
from pydantic import ValidationError

from extraction_models import (
    ExtractionResponseModel,
    InputQualityModel,
)


def test_image_quality_model_accepts_valid_input():
    quality = InputQualityModel(
        status="accepted",
        requires_review=False,
        input={
            "format": "PNG",
            "width": 1447,
            "height": 2048,
            "short_edge": 1447,
            "long_edge": 2048,
            "pixel_count": 2963456,
            "mode": "RGBA",
            "dpi": None,
        },
        warnings=[],
    )

    assert quality.status == "accepted"

    assert (
        quality.requires_review
        is False
    )

    assert quality.input.width == 1447
    assert quality.input.height == 2048


def test_native_pdf_quality_model_is_valid():
    quality = InputQualityModel(
        status="accepted",
        requires_review=False,
        input={
            "format": "PDF",
            "source": "native_pdf",
            "page_count": 4,
        },
        warnings=[],
    )

    assert quality.input.format == "PDF"

    assert quality.input.source == (
        "native_pdf"
    )

    assert quality.input.page_count == 4


def test_scanned_pdf_quality_model_is_valid():
    quality = InputQualityModel(
        status="review",
        requires_review=True,
        input={
            "format": "PDF",
            "source": "scanned_pdf",
            "page_count": 1,
            "pages": [
                {
                    "format": "PNG",
                    "width": 1239,
                    "height": 1754,
                    "short_edge": 1239,
                    "long_edge": 1754,
                    "pixel_count": 2172006,
                    "mode": "RGB",
                    "dpi": None,
                }
            ],
        },
        warnings=[
            {
                "code": (
                    "low_page_resolution"
                ),
                "message": (
                    "One or more PDF pages may "
                    "have insufficient resolution "
                    "for reliable OCR"
                ),
            }
        ],
    )

    assert quality.status == "review"

    assert (
        quality.requires_review
        is True
    )

    assert len(
        quality.input.pages
    ) == 1


def test_extraction_response_model_is_valid():
    response = ExtractionResponseModel(
        document_type="invoice",
        quality={
            "status": "accepted",
            "requires_review": False,
            "input": {
                "format": "PNG",
                "width": 1447,
                "height": 2048,
                "short_edge": 1447,
                "long_edge": 2048,
                "pixel_count": 2963456,
                "mode": "RGBA",
                "dpi": None,
            },
            "warnings": [],
        },
        raw_text="Test OCR text",
        llm_values={},
        final_values={
            "invoice_number": "0726592493",
            "total_amount": "67.96",
        },
        validation={
            "valid": True,
            "errors": {},
        },
    )

    assert response.document_type == "invoice"

    assert response.validation.valid is True

    assert response.final_values[
        "total_amount"
    ] == "67.96"


def test_invalid_quality_status_is_rejected():
    with pytest.raises(
        ValidationError,
    ):
        InputQualityModel(
            status="unknown",
            requires_review=False,
            input={
                "format": "PNG",
                "width": 1447,
                "height": 2048,
                "short_edge": 1447,
                "long_edge": 2048,
                "pixel_count": 2963456,
                "mode": "RGBA",
                "dpi": None,
            },
            warnings=[],
        )


def test_invalid_image_dimensions_are_rejected():
    with pytest.raises(
        ValidationError,
    ):
        InputQualityModel(
            status="accepted",
            requires_review=False,
            input={
                "format": "PNG",
                "width": 0,
                "height": 2048,
                "short_edge": 0,
                "long_edge": 2048,
                "pixel_count": 0,
                "mode": "RGBA",
                "dpi": None,
            },
            warnings=[],
        )


def test_unknown_quality_property_is_rejected():
    with pytest.raises(
        ValidationError,
    ):
        InputQualityModel(
            status="accepted",
            requires_review=False,
            input={
                "format": "PNG",
                "width": 1447,
                "height": 2048,
                "short_edge": 1447,
                "long_edge": 2048,
                "pixel_count": 2963456,
                "mode": "RGBA",
                "dpi": None,
            },
            warnings=[],
            unexpected_property=True,
        )