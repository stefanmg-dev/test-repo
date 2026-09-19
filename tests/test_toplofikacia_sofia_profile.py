from config_store import load_config
from document_config_resolver import resolve_document_fields
from extraction_orchestrator import apply_rules


TOPLOFIKACIA_TEXT = """
ФАКТУРА № 1204458225 - ОРИГИНАЛ
Дата на издаване/Дата на данъчно събитие - 31.08.2026 г.
ВСИЧКО по фактура: 15,12
Оставаща сума за плащане по фактура 1204458225 15,12 Евро
Срок за плащане на фактура № 1204458225 - 15.10.2026 г.
"""


def extract_toplofikacia_fields():
    config = load_config()
    document_config = config["invoice"]
    resolved_fields = resolve_document_fields(
        document_config=document_config,
        profile_name="heating_toplofikacia_sofia",
    )
    return apply_rules(
        document_type="invoice",
        config=config,
        raw_text=TOPLOFIKACIA_TEXT,
        llm_values={},
        resolved_fields=resolved_fields,
    )


def test_extracts_toplofikacia_issue_date_override():
    fields = extract_toplofikacia_fields()
    assert fields["issue_date"] == "31.08.2026"


def test_extracts_toplofikacia_due_date_override():
    fields = extract_toplofikacia_fields()
    assert fields["due_date"] == "15.10.2026"


def test_extracts_toplofikacia_total_amount_override():
    fields = extract_toplofikacia_fields()
    assert fields["total_amount"] == "15.12"
