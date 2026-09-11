from config_store import load_config
from extraction_orchestrator import apply_rules


A1_RAW_TEXT = """от 4
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
ПИН КОД ЗА ОНЛАЙН ПЛАЩАНЕ
1443
Фактура №0726592493
Период на фактуриране: 16.07.2026 - 15.08.2026
Обща стойност за плащане
67.96 €
Краен срок на плащане:
13.09.2026 г.

България ЕАД
A1
ЕИК:131468980 ДДС: BG131468980
Име: Адрес:
Стефан Момчилов Георгиев жк Красно село
Дата на издаване: 19.08.2026
Договор Ng: M5781970
Фактура Ng0726592493
"""


EXPECTED_VALUES = {
    "supplier_name": "А1 България ЕАД",
    "supplier_id": "131468980",
    "invoice_number": "0726592493",
    "issue_date": "19.08.2026",
    "contract_number": "М5781970",
    "customer_name": "Стефан Момчилов Георгиев",
    "customer_address": "жк.Красно село бл.201А вх.Г ет.2 ап.68",
    "due_date": "13.09.2026",
    "total_amount": "67.96",
}


def test_a1_invoice_extraction_regression():
    config = load_config()

    actual_values = apply_rules(
        document_type="invoice",
        config=config,
        raw_text=A1_RAW_TEXT,
        llm_values={}
    )

    assert actual_values == EXPECTED_VALUES