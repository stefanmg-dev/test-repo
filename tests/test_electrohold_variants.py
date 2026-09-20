import pytest

from config_store import load_config
from extraction_orchestrator import apply_rules
from supplier_profile_pipeline import (
    resolve_supplier_profile_fields,
)


EXPECTED_VALUES = {
    "supplier_name": "Електрохолд Продажби ЕАД",
    "supplier_id": "175133827",
    "invoice_number": "0484935637",
    "issue_date": "26.08.2026",
    "customer_name": "СТЕФАН МОМЧИЛОВ ГЕОРГИЕВ",
    "customer_address": (
        "бул. БРАТЯ БЪКСТОН, "
        "бл. 201 А, вх. Г, ап. 68"
    ),
    "due_date": "09.09.2026",
    "total_amount": "37.91",
    "client_number": "300031587847",
    "abonat_number": "9430804222",
    "total_consumption": None,
}


ELECTROHOLD_OCR_VARIANTS = [
    """
ФАКТУРА № 0484935637 / 26.08.2026
Доставчик Електрохолд Продажби ЕАД
Идент. № 175133827
Име СТЕФАН МОМЧИЛОВ ГЕОРГИЕВ Адрес бул. БРАТЯ БЪКСТОН, бл. 201 А, вх. Г, ап. 68
Обща стойност на сделката 37,91 €
Срок за плащане на фактурата от 26.08.2026 до 09.09.2026
electrohold.bg/sales
КЛИЕНТСКИ НОМЕР 300031587847
Абонатен № 9430804222
""".strip(),
    """
ФАКТУРА №0484935637/26.08.2026
ДОСТАВЧИК: ЕЛЕКТРОХОЛД ПРОДАЖБИ ЕАД
ЗДДС № BG175133827
Име   СТЕФАН   МОМЧИЛОВ   ГЕОРГИЕВ
Адрес   бул. БРАТЯ БЪКСТОН, бл. 201 А, вх. Г, ап. 68
Обща стойност на сделката
37,91 €
Срок за плащане на фактурата от 26.08.2026 до 09.09.2026
КЛИЕНТСКИ НОМЕР 300031587847
Абонатен № 9430804222
""".strip(),
    """
ФАКТУРА № 0484935637 / 26.08.2026
Електрохолд Продажби ЕАД
Идент. №175133827
Получател СТЕФАН МОМЧИЛОВ ГЕОРГИЕВ Адрес бул. БРАТЯ БЪКСТОН, бл. 201 А, вх. Г, ап. 68
Обща стойност на сделката 37.91 €
Срок за плащане на фактурата
от 26.08.2026 до 09.09.2026
КЛИЕНТСКИ НОМЕР 300031587847
Абонатен № 9430804222
""".strip(),
]


@pytest.mark.parametrize(
    "raw_text",
    ELECTROHOLD_OCR_VARIANTS,
)
def test_electrohold_common_fields_survive_ocr_variants(
    raw_text,
):
    config = load_config()

    profile_result = resolve_supplier_profile_fields(
        document_config=config["invoice"],
        ocr_text=raw_text,
    )

    assert profile_result["profile"] == (
        "electricity_electrohold"
    )

    final_values = apply_rules(
        document_type="invoice",
        config=config,
        raw_text=raw_text,
        llm_values={},
        resolved_fields=profile_result["fields"],
    )

    assert final_values == EXPECTED_VALUES
