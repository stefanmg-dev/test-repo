from profile_selection import (
    select_document_profile,
)
from supplier_matcher import (
    get_matched_profile_name,
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


def test_a1_match_selects_telecom_profile():
    matched_profile_name = (
        get_matched_profile_name(
            "Доставчик: А1 България ЕАД"
        )
    )

    selection = select_document_profile(
        document_config=DOCUMENT_CONFIG,
        matched_profile_name=(
            matched_profile_name
        ),
    )

    assert selection == {
        "profile": "telecom_a1",
        "use_default_profile": False,
        "requires_review": False,
        "warnings": [],
    }


def test_unknown_supplier_selects_common_only_mode():
    matched_profile_name = (
        get_matched_profile_name(
            "Непознат доставчик ООД"
        )
    )

    selection = select_document_profile(
        document_config=DOCUMENT_CONFIG,
        matched_profile_name=(
            matched_profile_name
        ),
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