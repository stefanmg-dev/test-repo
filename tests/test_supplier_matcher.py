import pytest

from supplier_matcher import (
    SupplierMatcherError,
    SupplierMatchResult,
    get_matched_profile_name,
    match_supplier,
    normalize_supplier_text,
)


@pytest.mark.parametrize(
    ("text", "expected_evidence"),
    [
        (
            "Доставчик: А1 България ЕАД",
            (
                "a1_bulgaria_company",
                "a1_bulgaria",
            ),
        ),
        (
            "Supplier: A1 Bulgaria EAD",
            (
                "a1_bulgaria_company",
                "a1_bulgaria",
            ),
        ),
        (
            "А1 България",
            (
                "a1_bulgaria",
            ),
        ),
        (
            "A1 Bulgaria",
            (
                "a1_bulgaria",
            ),
        ),
        (
            "Повече информация на www.a1.bg",
            (
                "a1_official_domain",
            ),
        ),
        (
            "https://a1.bg",
            (
                "a1_official_domain",
            ),
        ),
    ],
)
def test_matches_telecom_a1_from_clear_evidence(
    text,
    expected_evidence,
):
    result = match_supplier(text)

    assert result == SupplierMatchResult(
        profile_name="telecom_a1",
        evidence=expected_evidence,
    )


@pytest.mark.parametrize(
    "text",
    [
        "",
        "   ",
        "\n\t",
        "EVN България Електроснабдяване ЕАД",
        "Софийска вода АД",
        "Формат на страницата: A1",
        "Клетка A1",
        "Референция A123456",
        "example-a1.bg",
        "a1.bg.example.com",
    ],
)
def test_returns_none_without_clear_a1_evidence(
    text,
):
    result = match_supplier(text)

    assert result == SupplierMatchResult(
        profile_name=None,
        evidence=(),
    )


def test_matches_a1_with_irregular_whitespace():
    result = match_supplier(
        "Доставчик:\nА1    България\tЕАД"
    )

    assert result.profile_name == (
        "telecom_a1"
    )

    assert "a1_bulgaria_company" in (
        result.evidence
    )


def test_matching_is_case_insensitive():
    result = match_supplier(
        "a1 bulgaria ead"
    )

    assert result.profile_name == (
        "telecom_a1"
    )


def test_normalizes_unicode_and_whitespace():
    result = normalize_supplier_text(
        "  А1\n   България  "
    )

    assert result == "а1 българия"


def test_convenience_interface_returns_profile_name():
    profile_name = get_matched_profile_name(
        "Доставчик: А1 България ЕАД"
    )

    assert profile_name == "telecom_a1"


def test_convenience_interface_returns_none():
    profile_name = get_matched_profile_name(
        "Непознат доставчик ООД"
    )

    assert profile_name is None


@pytest.mark.parametrize(
    "invalid_text",
    [
        None,
        123,
        [],
        {},
    ],
)
def test_rejects_non_string_supplier_text(
    invalid_text,
):
    with pytest.raises(
        SupplierMatcherError,
        match="must be a string",
    ):
        match_supplier(invalid_text)

def test_matches_reversed_a1_ocr_company_block():
    result = match_supplier(
        "България ЕАД\nA1"
    )

    assert result.profile_name == (
        "telecom_a1"
    )

    assert (
        "a1_bulgaria_company_reversed"
        in result.evidence
    )



@pytest.mark.parametrize(
    ("text", "expected_evidence"),
    [
        (
            "Доставчик: Електрохолд Продажби ЕАД",
            (
                "electrohold_sales_company",
            ),
        ),
        (
            "Информация: electrohold.bg/sales",
            (
                "electrohold_official_domain",
            ),
        ),
        (
            "ЕЛЕКТРОХОЛД   ПРОДАЖБИ\nЕАД",
            (
                "electrohold_sales_company",
            ),
        ),
    ],
)
def test_matches_electricity_electrohold(
    text,
    expected_evidence,
):
    result = match_supplier(text)

    assert result == SupplierMatchResult(
        profile_name=(
            "electricity_electrohold"
        ),
        evidence=expected_evidence,
    )


def test_conflicting_supplier_evidence_returns_none():
    result = match_supplier(
        "А1 България ЕАД\n"
        "Електрохолд Продажби ЕАД"
    )

    assert result.profile_name is None
    assert result.evidence


@pytest.mark.parametrize(
    ("text", "expected_evidence"),
    [
        (
            "ДОСТАВЧИК: „ТОПЛОФИКАЦИЯ СОФИЯ“ ЕАД",
            ("toplofikacia_sofia_company",),
        ),
        (
            "Информация: www.toplo.bg",
            ("toplofikacia_sofia_domain",),
        ),
    ],
)
def test_matches_heating_toplofikacia_sofia(
    text,
    expected_evidence,
):
    result = match_supplier(text)
    assert result == SupplierMatchResult(
        profile_name="heating_toplofikacia_sofia",
        evidence=expected_evidence,
    )


def test_three_supplier_evidences_are_conflicting():
    result = match_supplier(
        "А1 България ЕАД\n"
        "Електрохолд Продажби ЕАД\n"
        "Топлофикация София ЕАД"
    )
    assert result.profile_name is None
    assert result.evidence
