import pytest

from config_store import load_config
from extraction_orchestrator import apply_rules
from supplier_profile_pipeline import (
    resolve_supplier_profile_fields,
)


EXPECTED_VALUES = {
    "supplier_name": "Топлофикация София ЕАД",
    "supplier_id": "831609046",
    "invoice_number": "1204458225",
    "issue_date": "31.08.2026",
    "customer_name": "СТЕФАН МОМЧИЛОВ ГЕОРГИЕВ",
    "customer_address": (
        "ГР. СОФИЯ 1618 КРАСНО СЕЛО "
        "БЛ. 201-А ВХ. 4 АПАРТАМЕНТ 68"
    ),
    "due_date": "15.10.2026",
    "total_amount": "15.12",
    "business_partner_number": "1000215239",
    "contract_account_number": "002100047756",
    "installation_number": "4000374298",
}


TOPLOFIKACIA_OCR_VARIANTS = [
    """
ДОСТАВЧИК: „ТОПЛОФИКАЦИЯ СОФИЯ“ ЕАД
ЕИК: 831609046
ПОЛУЧАТЕЛ: СТЕФАН МОМЧИЛОВ ГЕОРГИЕВ
ГР. СОФИЯ 1618 КРАСНО СЕЛО
БЛ. 201-А ВХ. 4 АПАРТАМЕНТ 68
БИЗНЕС ПАРТНЬОР №1000215239
ДОГОВОРНА СМЕТКА №002100047756
НОМЕР НА ИНСТАЛАЦИЯ №4000374298
ФАКТУРА № 1204458225 - ОРИГИНАЛ
Дата на издаване/Дата на данъчно събитие - 31.08.2026 г.
ВСИЧКО по фактура: 15,12
Срок за плащане на фактура № 1204458225 - 15.10.2026 г.
www.toplo.bg
""".strip(),
    """
ТОПЛОФИКАЦИЯ   СОФИЯ ЕАД
ЕИК:831609046
ПОЛУЧАТЕЛ:   СТЕФАН   МОМЧИЛОВ   ГЕОРГИЕВ
ГР. СОФИЯ 1618 КРАСНО СЕЛО БЛ. 201-А ВХ. 4 АПАРТАМЕНТ 68
БИЗНЕС   ПАРТНЬОР № 1000215239
ДОГОВОРНА   СМЕТКА № 002100047756
НОМЕР   НА   ИНСТАЛАЦИЯ № 4000374298
Фактура №1204458225
Дата на издаване/Дата на данъчно събитие - 31.08.2026
ВСИЧКО   по   фактура : 15.12
Срок за плащане на фактура №1204458225 - 15.10.2026
""".strip(),
    """
Информация: www.toplo.bg
ЕИК: 831609046
ПОЛУЧАТЕЛ: СТЕФАН МОМЧИЛОВ ГЕОРГИЕВ
ГР. СОФИЯ 1618 КРАСНО СЕЛО
БЛ. 201-А ВХ. 4 АПАРТАМЕНТ 68
БИЗНЕС ПАРТНЬОР НОМЕР 1000215239
ДОГОВОРНА СМЕТКА: 002100047756
ИНСТАЛАЦИЯ №4000374298
ФАКТУРА № 1204458225
Дата на издаване - 31.08.2026
Оставаща сума за плащане по фактура 1204458225 15,12
Срок за плащане на фактура № 1204458225 - 15.10.2026
""".strip(),
]


@pytest.mark.parametrize(
    "raw_text",
    TOPLOFIKACIA_OCR_VARIANTS,
)
def test_toplofikacia_fields_survive_ocr_variants(
    raw_text,
):
    config = load_config()

    profile_result = resolve_supplier_profile_fields(
        document_config=config["invoice"],
        ocr_text=raw_text,
    )

    assert profile_result["profile"] == (
        "heating_toplofikacia_sofia"
    )

    final_values = apply_rules(
        document_type="invoice",
        config=config,
        raw_text=raw_text,
        llm_values={},
        resolved_fields=profile_result["fields"],
    )

    assert final_values == EXPECTED_VALUES
