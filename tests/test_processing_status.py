import pytest

from routes_extract import determine_processing_status


@pytest.mark.parametrize(
    (
        "validation_valid",
        "requires_review",
        "expected_status",
    ),
    [
        (
            True,
            False,
            "accepted",
        ),
        (
            True,
            True,
            "review",
        ),
        (
            False,
            False,
            "invalid",
        ),
        (
            False,
            True,
            "invalid",
        ),
    ],
)
def test_determine_processing_status(
    validation_valid,
    requires_review,
    expected_status,
):
    validation = {
        "valid": validation_valid,
        "errors": {},
    }

    quality = {
        "requires_review": requires_review,
    }

    assert determine_processing_status(
        validation=validation,
        quality=quality,
    ) == expected_status
