from config_store import load_config
from extraction_orchestrator import apply_rules


RAW_TEXT = """
от 4
1
Иван Тестов Примеров
София
19.08.2026
19.08.2026
M1234567
Адрес:
Име:
Дата на дан. събитие:
Място на издаване:
Дата на издаване:
Договор №:
жк.Тестов квартал бл.10 вх.А ет.2 ап.3
1000 София

Фактура №0123456789
Краен срок на плащане:
13.09.2026 г.
Обща стойност за плащане
67.96 €

България ЕАД
ЕИК:131468980
Име: Адрес:
Иван Тестов Примеров жк Тестов квартал бл.11 вх А ет 2 ап.3 1000 София
Дата на издаване: 19.08.2026
Договор Ng: M1234567
Фактура Ng0123456789
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
        "Иван Тестов Примеров"
    )

    assert values["customer_address"] == (
        "жк.Тестов квартал "
        "бл.10 вх.А ет.2 ап.3"
    )
