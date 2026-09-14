from config_store import load_config
from extraction_orchestrator import apply_rules


RAW_TEXT = """
А1 България" ЕАД
Сошия 309 ул: "Кукуш' тел : *88,+359 88 123
ЕИК:131468980 ДДС: BG131468980

Име: Адрес:
Стефан Момчилов Георгиев жК Красно село бл.207A вх Г ет .2 ап.68 1000 София

Дата на дан_ събитие: 19.08.2026
Дата на издаване: 19.08.2026
Място на издаване: София
Договор Ng: М5781970
Фактура Ng0726592493

Краен срок на плащане: 13.09.2026

Обща стойност за плащане
67.96
""".strip()


def test_combined_name_and_address_line_is_separated():
    config = load_config()

    values = apply_rules(
        document_type="invoice",
        config=config,
        raw_text=RAW_TEXT,
        llm_values={},
    )

    assert values["customer_name"] == (
        "Стефан Момчилов Георгиев"
    )

    assert values["customer_address"] == (
        "жК Красно село "
        "бл.207A вх Г ет .2 ап.68"
    )


def test_low_quality_png_address_does_not_include_name():
    config = load_config()

    values = apply_rules(
        document_type="invoice",
        config=config,
        raw_text=RAW_TEXT,
        llm_values={},
    )

    assert not values["customer_address"].startswith(
        "Стефан"
    )
