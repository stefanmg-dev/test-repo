import pytest

from profile_selection import (
    ProfileSelectionError,
    select_document_profile,
)


DOCUMENT_CONFIG = {
    "default_profile": "telecom_a1",
    "common_fields": [],
    "profiles": {
        "telecom_a1": {
            "fields": [],
        },
        "electricity_evn": {
            "fields": [],
        },
    },
}


def test_selects_known_profile():
    selection = select_document_profile(
        document_config=DOCUMENT_CONFIG,
        matched_profile_name="telecom_a1",
    )

    assert selection == {
        "profile": "telecom_a1",
        "use_default_profile": False,
        "requires_review": False,
        "warnings": [],
    }


def test_selects_another_known_profile():
    selection = select_document_profile(
        document_config=DOCUMENT_CONFIG,
        matched_profile_name="electricity_evn",
    )

    assert selection["profile"] == (
        "electricity_evn"
    )

    assert selection[
        "requires_review"
    ] is False

    assert selection["warnings"] == []


def test_unknown_supplier_uses_common_only_mode():
    selection = select_document_profile(
        document_config=DOCUMENT_CONFIG,
        matched_profile_name=None,
    )

    assert selection == {
        "profile": None,
        "use_default_profile": False,
        "requires_review": True,
        "warnings": [
            {
                "code": (
                    "unknown_supplier_profile"
                ),
                "message": (
                    "No matching supplier profile "
                    "was found"
                ),
            }
        ],
    }


def test_unknown_supplier_does_not_use_default_profile():
    selection = select_document_profile(
        document_config=DOCUMENT_CONFIG,
        matched_profile_name=None,
    )

    assert selection["profile"] is None

    assert selection[
        "use_default_profile"
    ] is False


def test_rejects_unknown_profile_name():
    with pytest.raises(
        ProfileSelectionError,
        match="was not found",
    ):
        select_document_profile(
            document_config=DOCUMENT_CONFIG,
            matched_profile_name=(
                "unknown_profile"
            ),
        )


@pytest.mark.parametrize(
    "invalid_profile_name",
    [
        "",
        "   ",
        123,
    ],
)
def test_rejects_invalid_profile_name(
    invalid_profile_name,
):
    with pytest.raises(
        ProfileSelectionError,
        match="non-empty string",
    ):
        select_document_profile(
            document_config=DOCUMENT_CONFIG,
            matched_profile_name=(
                invalid_profile_name
            ),
        )


def test_rejects_invalid_profiles_configuration():
    with pytest.raises(
        ProfileSelectionError,
        match="'profiles' must be an object",
    ):
        select_document_profile(
            document_config={
                "common_fields": [],
                "profiles": [],
            },
            matched_profile_name=None,
        )
