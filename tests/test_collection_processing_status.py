import pytest

from routes_extract import determine_processing_status


@pytest.mark.parametrize(
    (
        "validation",
        "collection_validation",
        "quality",
        "expected",
    ),
    [
        (
            {"valid": False},
            {"valid": True},
            {"requires_review": False},
            "invalid",
        ),
        (
            {"valid": True},
            {"valid": False},
            {"requires_review": False},
            "invalid",
        ),
        (
            {"valid": True},
            {"valid": True},
            {"requires_review": True},
            "review",
        ),
        (
            {"valid": True},
            {"valid": True},
            {"requires_review": False},
            "accepted",
        ),
    ],
)
def test_processing_status_includes_collection_validation(
    validation,
    collection_validation,
    quality,
    expected,
):
    assert determine_processing_status(
        validation=validation,
        collection_validation=collection_validation,
        quality=quality,
    ) == expected


def test_processing_status_keeps_legacy_call_compatible():
    assert determine_processing_status(
        validation={"valid": True},
        quality={"requires_review": False},
    ) == "accepted"
