import pytest

from config_store import load_config
from extraction_orchestrator import apply_rules


BASE_TEXT = """
"А1 България" ЕАД
ЕИК: 131468980

Име: Стефан Момчилов Георгиев
Адрес: жк Красно село бл.201А вх.Г ет 2 ап. 68

Дата на издаване: 19.08.2026
Договор Ng: M5781970
Фактура Ng0726592493

Краен срок на плащане: 13.09.2026

{amount_block}
""".strip()


@pytest.mark.parametrize(
    (
        "amount_block",
        "expected_amount",
    ),
    [
        (
            "Обща стойност за плащане 67.96",
            "67.96",
        ),
        (
            (
                "Обща стойност за плащане\n"
                "67.96"
            ),
            "67.96",
        ),
        (
            (
                "Обща стойност за плащане\n"
                "67.96 €"
            ),
            "67.96",
        ),
        (
            (
                "Обща стойност за плащане   "
                "67.96 лв."
            ),
            "67.96",
        ),
        (
            "Обща стойност за плащане 67,96",
            "67.96",
        ),
        (
            (
                "Обща стойност за плащане\n"
                "67,96 €"
            ),
            "67.96",
        ),
    ],
)
def test_a1_total_amount_variants(
    amount_block,
    expected_amount,
):
    config = load_config()

    raw_text = BASE_TEXT.format(
        amount_block=amount_block
    )

    values = apply_rules(
        document_type="invoice",
        config=config,
        raw_text=raw_text,
        llm_values={},
    )

    assert values["total_amount"] == (
        expected_amount
    )
