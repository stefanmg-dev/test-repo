import pytest

from config_store import load_config
from extraction_orchestrator import apply_rules
from result_validator import validate_result


A1_OCR_VARIANTS = [
    """
"А1 България" ЕАД
ЕИК:131468980

Име: Стефан Момчилов Георгиев
Адрес: жк Красно село бл.201А вх.Г ет 2 ап. 68

Дата на издаване: 19.08.2026
Договор Ng: M5781970
Фактура Ng0726592493

Краен срок на плащане: 13.09.2026

Обща стойност за плащане
67.96 €
""".strip(),
    """
"А1 България" ЕАД
ДДС: BG131468980

Име:
Стефан Момчилов Георгиев

Адрес:
жк.Красно село бл.201А вх.Г ет.2 ап.68

19.08.2026 Дата на издаване
Договор № М5781970
Фактура № 0726592493

Краен срок на плащане:
13.09.2026

Обща стойност за плащане
67,96 €
""".strip(),
]


EXPECTED_COMMON_VALUES = {
    "supplier_name": "А1 България ЕАД",
    "supplier_id": "131468980",
    "invoice_number": "0726592493",
    "issue_date": "19.08.2026",
    "customer_name": "Стефан Момчилов Георгиев",
    "due_date": "13.09.2026",
    "total_amount": "67.96",
}


@pytest.mark.parametrize(
    "raw_text",
    A1_OCR_VARIANTS,
)
def test_a1_variants_are_extracted_and_validated(
    raw_text,
):
    config = load_config()

    invoice_config = config["invoice"]

    assert invoice_config[
        "default_profile"
    ] == "telecom_a1"

    final_values = apply_rules(
        document_type="invoice",
        config=config,
        raw_text=raw_text,
        llm_values={},
    )

    assert len(final_values) == 9

    for field_name, expected_value in (
        EXPECTED_COMMON_VALUES.items()
    ):
        assert final_values[field_name] == (
            expected_value
        )

    assert final_values[
        "contract_number"
    ] in {
        "M5781970",
        "М5781970",
    }

    assert final_values[
        "customer_address"
    ] in {
        (
            "жк Красно село "
            "бл.201А вх.Г ет 2 ап. 68"
        ),
        (
            "жк.Красно село "
            "бл.201А вх.Г ет.2 ап.68"
        ),
    }

    validation = validate_result(
        document_type="invoice",
        config=config,
        final_values=final_values,
    )

    assert validation == {
        "valid": True,
        "errors": {},
    }


def test_a1_incomplete_document_is_invalid_end_to_end():
    config = load_config()

    raw_text = """
"А1 България" ЕАД
ЕИК:131468980

Име: Стефан Момчилов Георгиев
Адрес: жк Красно село бл.201А вх.Г ет 2 ап. 68

Дата на издаване: 19.08.2026

Краен срок на плащане: 13.09.2026
""".strip()

    final_values = apply_rules(
        document_type="invoice",
        config=config,
        raw_text=raw_text,
        llm_values={},
    )

    validation = validate_result(
        document_type="invoice",
        config=config,
        final_values=final_values,
    )

    assert validation["valid"] is False

    assert {
        "invoice_number",
        "contract_number",
        "total_amount",
    }.issubset(
        validation["errors"]
    )
