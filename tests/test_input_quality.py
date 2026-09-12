import pytest

from input_quality import (
    QUALITY_STATUS_ACCEPTED,
    QUALITY_STATUS_REVIEW,
    build_image_input_metadata,
    evaluate_image_quality,
    normalize_dpi,
)


def test_accepted_quality_for_2048_pixel_image():
    quality = evaluate_image_quality(
        image_format="PNG",
        width=1447,
        height=2048,
        mode="RGBA",
        dpi=None,
    )

    assert quality == {
        "status": QUALITY_STATUS_ACCEPTED,
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
    }


def test_review_quality_for_1754_pixel_image():
    quality = evaluate_image_quality(
        image_format="PNG",
        width=1239,
        height=1754,
        mode="RGBA",
        dpi=None,
    )

    assert quality["status"] == (
        QUALITY_STATUS_REVIEW
    )

    assert quality["requires_review"] is True

    assert quality["warnings"] == [
        {
            "code": "low_image_resolution",
            "message": (
                "Image resolution may be "
                "insufficient for reliable OCR"
            ),
        }
    ]


def test_orientation_does_not_change_quality():
    portrait_quality = evaluate_image_quality(
        image_format="PNG",
        width=1447,
        height=2048,
        mode="RGB",
    )

    landscape_quality = evaluate_image_quality(
        image_format="PNG",
        width=2048,
        height=1447,
        mode="RGB",
    )

    assert (
        portrait_quality["status"]
        == landscape_quality["status"]
        == QUALITY_STATUS_ACCEPTED
    )

    assert (
        portrait_quality["input"][
            "short_edge"
        ]
        == landscape_quality["input"][
            "short_edge"
        ]
        == 1447
    )


def test_valid_dpi_is_normalized():
    assert normalize_dpi(
        (199.9996, 200.001)
    ) == [
        200.0,
        200.0,
    ]


def test_missing_or_invalid_dpi_returns_none():
    assert normalize_dpi(None) is None
    assert normalize_dpi("200") is None
    assert normalize_dpi((200,)) is None
    assert normalize_dpi((0, 200)) is None


def test_invalid_dimensions_are_rejected():
    with pytest.raises(
        ValueError,
        match="dimensions must be positive",
    ):
        build_image_input_metadata(
            image_format="PNG",
            width=0,
            height=2048,
            mode="RGBA",
        )