from config_store import load_config
from document_config_resolver import resolve_document_fields
from extraction_orchestrator import apply_rules


TOPLOFIKACIA_TEXT = """
ПОЛУЧАТЕЛ: ТЕСТОВ КЛИЕНТ ПРИМЕРЕН ГР. СОФИЯ 1618 КРАСНО СЕЛО БЛ. 201-А ВХ. 4 АПАРТАМЕНТ 68 БИЗНЕС ПАРТНЬОР №1000215239 ДОГОВОРНА СМЕТКА №002100047756 НОМЕР НА ИНСТАЛАЦИЯ №4000374298
ФАКТУРА № 1204458225 - ОРИГИНАЛ
Дата на издаване/Дата на данъчно събитие - 31.08.2026 г.
ВСИЧКО по фактура: 15,12
Оставаща сума за плащане по фактура 1204458225 15,12 Евро
Срок за плащане на фактура № 1204458225 - 15.10.2026 г.
"""


def extract_toplofikacia_fields():
    config = load_config()
    document_config = config["invoice"]
    resolved_fields = resolve_document_fields(
        document_config=document_config,
        profile_name="heating_toplofikacia_sofia",
    )
    return apply_rules(
        document_type="invoice",
        config=config,
        raw_text=TOPLOFIKACIA_TEXT,
        llm_values={},
        resolved_fields=resolved_fields,
    )


def test_extracts_toplofikacia_issue_date_override():
    fields = extract_toplofikacia_fields()
    assert fields["issue_date"] == "31.08.2026"


def test_extracts_toplofikacia_due_date_override():
    fields = extract_toplofikacia_fields()
    assert fields["due_date"] == "15.10.2026"


def test_extracts_toplofikacia_total_amount_override():
    fields = extract_toplofikacia_fields()
    assert fields["total_amount"] == "15.12"



def test_extracts_toplofikacia_customer_name_override():
    fields = extract_toplofikacia_fields()
    assert fields["customer_name"] == "ТЕСТОВ КЛИЕНТ ПРИМЕРЕН"


def test_extracts_toplofikacia_customer_address_override():
    fields = extract_toplofikacia_fields()
    assert fields["customer_address"] == (
        "ГР. СОФИЯ 1618 КРАСНО СЕЛО БЛ. 201-А ВХ. 4 "
        "АПАРТАМЕНТ 68"
    )


def test_extracts_toplofikacia_business_partner_number():
    fields = extract_toplofikacia_fields()
    assert fields["business_partner_number"] == "1000215239"


def test_extracts_toplofikacia_contract_account_number():
    fields = extract_toplofikacia_fields()
    assert fields["contract_account_number"] == "002100047756"


def test_extracts_toplofikacia_installation_number():
    fields = extract_toplofikacia_fields()
    assert fields["installation_number"] == "4000374298"


FULL_TOPLOFIKACIA_TEXT = """
ДОСТАВЧИК: „ТОПЛОФИКАЦИЯ СОФИЯ“ ЕАД
ЕИК: 123456789
№ ПО ДДС: BG123456789

ПОЛУЧАТЕЛ: ТЕСТОВ КЛИЕНТ ПРИМЕРЕН
ГР. СОФИЯ 1618 КРАСНО СЕЛО БЛ. 201-А ВХ. 4 АПАРТАМЕНТ 68
БИЗНЕС ПАРТНЬОР №1000000001
ДОГОВОРНА СМЕТКА №002100000001
НОМЕР НА ИНСТАЛАЦИЯ №4000000001

ФАКТУРА № 1200000001 - ОРИГИНАЛ
Дата на издаване/Дата на данъчно събитие - 31.08.2026 г.

ВСИЧКО по фактура: 15,12
Оставаща сума за плащане по фактура 1200000001 15,12 Евро
Срок за плащане на фактура № 1200000001 - 15.10.2026 г.
"""


def test_extracts_complete_toplofikacia_profile():
    config = load_config()
    resolved_fields = resolve_document_fields(
        document_config=config["invoice"],
        profile_name="heating_toplofikacia_sofia",
    )

    fields = apply_rules(
        document_type="invoice",
        config=config,
        raw_text=FULL_TOPLOFIKACIA_TEXT,
        llm_values={},
        resolved_fields=resolved_fields,
    )

    expected = {
        "supplier_name": "Топлофикация София ЕАД",
        "supplier_id": "123456789",
        "invoice_number": "1200000001",
        "issue_date": "31.08.2026",
        "customer_name": "ТЕСТОВ КЛИЕНТ ПРИМЕРЕН",
        "customer_address": (
            "ГР. СОФИЯ 1618 КРАСНО СЕЛО БЛ. 201-А ВХ. 4 "
            "АПАРТАМЕНТ 68"
        ),
        "due_date": "15.10.2026",
        "total_amount": "15.12",
        "business_partner_number": "1000000001",
        "contract_account_number": "002100000001",
        "installation_number": "4000000001",
    }

    for field_name, expected_value in expected.items():
        assert fields[field_name] == expected_value
