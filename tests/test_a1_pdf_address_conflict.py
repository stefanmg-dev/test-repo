from config_store import load_config
from extraction_orchestrator import apply_rules


RAW_TEXT = """
от 4
1
Стефан Момчилов Георгиев
София
19.08.2026
19.08.2026
М5781970
Адрес:
Имe:
Дата на дан. събитие:
Място на издаване:
Дата на издаване:
Договор №:
жк.Красно село бл.201А вх.Г ет.2 ап.68
1000 София

Фактура №0726592493
Краен срок на плащане:
13.09.2026 г.
Обща стойност за плащане
67.96 €

България ЕАД
ЕИК:131468980
Име: Адрес:
Стефан Момчилов Георгиев жк Красно село бл.207А вх Г ет 2 ап.68 1000 София
Дата на издаване: 19.08.2026
Договор Ng: M5781970
Фактура Ng0726592493
Краен срок на плащане: 13.09.2026 г.
Обща стойност за плащане
67.96 €
""".strip()


def test_native_pdf_address_wins_over_ocr_conflict():
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
        "жк.Красно село "
        "бл.201А вх.Г ет.2 ап.68"
    )
