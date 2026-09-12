from typing import Any


QUALITY_STATUS_ACCEPTED = "accepted"
QUALITY_STATUS_REVIEW = "review"

MIN_ACCEPTED_SHORT_EDGE = 1400
MIN_ACCEPTED_LONG_EDGE = 2000


def normalize_dpi(
    dpi: Any,
) -> list[float] | None:
    if not isinstance(dpi, (tuple, list)):
        return None

    if len(dpi) != 2:
        return None

    try:
        horizontal_dpi = float(dpi[0])
        vertical_dpi = float(dpi[1])

    except (
        TypeError,
        ValueError,
    ):
        return None

    if (
        horizontal_dpi <= 0
        or vertical_dpi <= 0
    ):
        return None

    return [
        round(horizontal_dpi, 2),
        round(vertical_dpi, 2),
    ]


def build_image_input_metadata(
    *,
    image_format: str | None,
    width: int,
    height: int,
    mode: str | None,
    dpi: Any = None,
) -> dict:
    if width <= 0 or height <= 0:
        raise ValueError(
            "Image dimensions must be positive"
        )

    return {
        "format": (
            image_format.upper()
            if image_format
            else None
        ),
        "width": width,
        "height": height,
        "short_edge": min(
            width,
            height,
        ),
        "long_edge": max(
            width,
            height,
        ),
        "pixel_count": width * height,
        "mode": mode,
        "dpi": normalize_dpi(dpi),
    }


def assess_image_quality(
    input_metadata: dict,
) -> dict:
    short_edge = input_metadata[
        "short_edge"
    ]

    long_edge = input_metadata[
        "long_edge"
    ]

    warnings = []

    if (
        short_edge < MIN_ACCEPTED_SHORT_EDGE
        or long_edge < MIN_ACCEPTED_LONG_EDGE
    ):
        warnings.append(
            {
                "code": "low_image_resolution",
                "message": (
                    "Image resolution may be "
                    "insufficient for reliable OCR"
                ),
            }
        )

    requires_review = bool(warnings)

    return {
        "status": (
            QUALITY_STATUS_REVIEW
            if requires_review
            else QUALITY_STATUS_ACCEPTED
        ),
        "requires_review": requires_review,
        "input": input_metadata,
        "warnings": warnings,
    }


def evaluate_image_quality(
    *,
    image_format: str | None,
    width: int,
    height: int,
    mode: str | None,
    dpi: Any = None,
) -> dict:
    input_metadata = build_image_input_metadata(
        image_format=image_format,
        width=width,
        height=height,
        mode=mode,
        dpi=dpi,
    )

    return assess_image_quality(
        input_metadata
    )