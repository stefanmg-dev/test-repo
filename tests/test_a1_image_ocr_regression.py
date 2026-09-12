from config_store import load_config
from extraction_orchestrator import apply_rules


A1_IMAGE_OCR_TEXT = """
"А1 България" ЕАД
ЕИК:131468980 ДДС: BG131468980

Име: Стефан Момчилов Георгиев
Адрес: жк Красно село бл.201А вх.Г ет 2 ап. 68 1000 София

Дата на дан. събитие: 19.08.2026
Дата на издаване: 19.08.2026
Място на издаване: София
Договор Ng: M5781970

Фактура Ng0726592493
Период на фактуриране: 16.07.2026 15.08.2026

СТОЙНОСТ ЗА ПЛАЩАНЕ
67.96 €

ПЛАТЕТЕ ДО 13.09.2026

Обща стойност на фактурата
67.96 €

Краен срок на плащане: 13.09.2026 г.

Обща стойност за плащане
67.96 €
""".strip()


EXPECTED_VALUES = {
    "supplier_name": "А1 България ЕАД",
    "supplier_id": "131468980",
    "invoice_number": "0726592493",
    "issue_date": "19.08.2026",
    "contract_number": "M5781970",
    "customer_name": "Стефан Момчилов Георгиев",
    "customer_address": (
        "жк Красно село бл.201А вх.Г ет 2 ап. 68"
    ),
    "due_date": "13.09.2026",
    "total_amount": "67.96",
}


def test_a1_image_ocr_extraction_regression():
    config = load_config()

    final_values = apply_rules(
        document_type="invoice",
        config=config,
        raw_text=A1_IMAGE_OCR_TEXT,
        llm_values={},
    )

    assert final_values == EXPECTED_VALUES