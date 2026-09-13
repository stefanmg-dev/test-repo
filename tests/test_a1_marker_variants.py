import pytest

from config_store import load_config
from extraction_orchestrator import apply_rules


BASE_TEXT = """
"А1 България" ЕАД
ЕИК: 131468980

Име: Стефан Момчилов Георгиев
Адрес: жк Красно село бл.201А вх.Г ет 2 ап. 68

Дата на дан. събитие: 19.08.2026
Дата на издаване: 19.08.2026

{contract_line}
{invoice_line}

Краен срок на плащане: 13.09.2026 г.

Обща стойност за плащане
67.96
""".strip()


@pytest.mark.parametrize(
    (
        "invoice_line",
        "expected_invoice_number",
    ),
    [
        (
            "Фактура №0726592493",
            "0726592493",
        ),
        (
            "Фактура № 0726592493",
            "0726592493",
        ),
        (
            "Фактура Ng0726592493",
            "0726592493",
        ),
        (
            "Фактура Ng 0726592493",
            "0726592493",
        ),
        (
            "Фактура No 0726592493",
            "0726592493",
        ),
        (
            "Фактура 0726592493",
            "0726592493",
        ),
    ],
)
def test_a1_invoice_number_marker_variants(
    invoice_line,
    expected_invoice_number,
):
    config = load_config()

    raw_text = BASE_TEXT.format(
        invoice_line=invoice_line,
        contract_line=(
            "Договор Ng: M5781970"
        ),
    )

    values = apply_rules(
        document_type="invoice",
        config=config,
        raw_text=raw_text,
        llm_values={},
    )

    assert values["invoice_number"] == (
        expected_invoice_number
    )


@pytest.mark.parametrize(
    (
        "contract_line",
        "expected_contract_number",
    ),
    [
        (
            "Договор № M5781970",
            "M5781970",
        ),
        (
            "Договор Ng M5781970",
            "M5781970",
        ),
        (
            "Договор Ng: M5781970",
            "M5781970",
        ),
        (
            "Договор: M5781970",
            "M5781970",
        ),
        (
            "Договор № М5781970",
            "М5781970",
        ),
        (
            "Договор\nM5781970",
            "M5781970",
        ),
    ],
)
def test_a1_contract_number_marker_variants(
    contract_line,
    expected_contract_number,
):
    config = load_config()

    raw_text = BASE_TEXT.format(
        invoice_line=(
            "Фактура Ng0726592493"
        ),
        contract_line=contract_line,
    )

    values = apply_rules(
        document_type="invoice",
        config=config,
        raw_text=raw_text,
        llm_values={},
    )

    assert values["contract_number"] == (
        expected_contract_number
    )