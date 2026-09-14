import pytest

from config_store import load_config
from extraction_orchestrator import apply_rules


BASE_TEXT = """
"А1 България" ЕАД
ЕИК: 131468980

{name_block}
{address_block}

Дата на издаване: 19.08.2026
Договор Ng: M5781970
Фактура Ng0726592493

Краен срок на плащане: 13.09.2026

Обща стойност за плащане
67.96
""".strip()


def extract_values(
    name_block: str,
    address_block: str,
) -> dict:
    config = load_config()

    raw_text = BASE_TEXT.format(
        name_block=name_block,
        address_block=address_block,
    )

    return apply_rules(
        document_type="invoice",
        config=config,
        raw_text=raw_text,
        llm_values={},
    )


@pytest.mark.parametrize(
    "name_block",
    [
        (
            "Име: Стефан Момчилов "
            "Георгиев"
        ),
        (
            "Име:\n"
            "Стефан Момчилов Георгиев"
        ),
        (
            "Име:   Стефан Момчилов "
            "Георгиев"
        ),
        (
            "Име:\tСтефан Момчилов "
            "Георгиев"
        ),
    ],
)
def test_a1_customer_name_variants(
    name_block,
):
    values = extract_values(
        name_block=name_block,
        address_block=(
            "Адрес: жк Красно село "
            "бл.201А вх.Г ет 2 ап. 68"
        ),
    )

    assert values["customer_name"] == (
        "Стефан Момчилов Георгиев"
    )


@pytest.mark.parametrize(
    (
        "address_block",
        "expected_address",
    ),
    [
        (
            (
                "Адрес: жк Красно село "
                "бл.201А вх.Г ет 2 ап. 68"
            ),
            (
                "жк Красно село "
                "бл.201А вх.Г ет 2 ап. 68"
            ),
        ),
        (
            (
                "Адрес: жк.Красно село "
                "бл.201А вх.Г ет.2 ап.68"
            ),
            (
                "жк.Красно село "
                "бл.201А вх.Г ет.2 ап.68"
            ),
        ),
        (
            (
                "Адрес: ж.к. Красно село "
                "бл.201А вх.Г ет. 2 ап. 68"
            ),
            (
                "ж.к. Красно село "
                "бл.201А вх.Г ет. 2 ап. 68"
            ),
        ),
        (
            (
                "Адрес:\n"
                "жк Красно село бл.201А "
                "вх.Г ет 2 ап 68"
            ),
            (
                "жк Красно село бл.201А "
                "вх.Г ет 2 ап 68"
            ),
        ),
        (
            (
                "Адрес:   жк Красно село "
                "бл.201А вх.Г ет.2 ап. 68"
            ),
            (
                "жк Красно село "
                "бл.201А вх.Г ет.2 ап. 68"
            ),
        ),
        (
            (
                "Адрес: жк Красно село "
                "бл.201А вх.Г ет 2 ап.68 "
                "1000 София"
            ),
            (
                "жк Красно село "
                "бл.201А вх.Г ет 2 ап.68"
            ),
        ),
    ],
)
def test_a1_customer_address_variants(
    address_block,
    expected_address,
):
    values = extract_values(
        name_block=(
            "Име: Стефан Момчилов "
            "Георгиев"
        ),
        address_block=address_block,
    )

    assert values["customer_address"] == (
        expected_address
    )
