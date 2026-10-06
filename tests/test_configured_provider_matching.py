import pytest

from config_store import load_config
from supplier_matcher import (
    SupplierMatchResult,
    match_supplier,
    match_supplier_from_config,
)


@pytest.mark.parametrize(
    "text",
    [
        "Доставчик: А1 България ЕАД",
        "Supplier: A1 Bulgaria EAD",
        "България ЕАД\nA1",
        "Информация: www.a1.bg",
        "Доставчик: Електрохолд Продажби ЕАД",
        "Информация: electrohold.bg/sales",
        "ДОСТАВЧИК: „ТОПЛОФИКАЦИЯ СОФИЯ“ ЕАД",
        "Информация: www.toplo.bg",
        "Непознат доставчик ООД",
        (
            "А1 България ЕАД\n"
            "Електрохолд Продажби ЕАД"
        ),
    ],
)
def test_configured_matching_matches_legacy_behavior(text):
    invoice = load_config()["invoice"]
    assert match_supplier_from_config(invoice, text) == match_supplier(text)


def test_all_runtime_profiles_have_matching_configuration():
    profiles = load_config()["invoice"]["profiles"]
    assert set(profiles) == {
        "telecom_a1",
        "electricity_electrohold",
        "heating_toplofikacia_sofia",
    }
    assert all(profile.get("matching") for profile in profiles.values())


def test_unknown_supplier_remains_unmatched():
    invoice = load_config()["invoice"]
    assert match_supplier_from_config(
        invoice,
        "Софийска вода АД",
    ) == SupplierMatchResult(profile_name=None, evidence=())
