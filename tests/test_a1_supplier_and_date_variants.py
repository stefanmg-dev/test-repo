import pytest

from config_store import load_config
from extraction_orchestrator import apply_rules


BASE_TEXT = """
"А1 България" ЕАД
{supplier_line}

Име: Стефан Момчилов Георгиев
Адрес: жк Красно село бл.201А вх.Г ет 2 ап. 68

{issue_date_block}

Договор Ng: M5781970
Фактура Ng0726592493

{due_date_block}

Обща стойност за плащане
67.96
""".strip()


def extract_values(
    supplier_line,
    issue_date_block,
    due_date_block,
):
    config = load_config()

    raw_text = BASE_TEXT.format(
        supplier_line=supplier_line,
        issue_date_block=issue_date_block,
        due_date_block=due_date_block,
    )

    return apply_rules(
        document_type="invoice",
        config=config,
        raw_text=raw_text,
        llm_values={},
    )


@pytest.mark.parametrize(
    "supplier_line",
    [
        "ЕИК:131468980",
        "ЕИК: 131468980",
        "ЕИК 131468980",
        "ДДС: BG131468980",
        "ДДС BG131468980",
    ],
)
def test_a1_supplier_id_variants(
    supplier_line,
):
    values = extract_values(
        supplier_line=supplier_line,
        issue_date_block=(
            "Дата на дан. събитие: 19.08.2026\n"
            "Дата на издаване: 19.08.2026"
        ),
        due_date_block=(
            "Краен срок на плащане: "
            "13.09.2026"
        ),
    )

    assert values["supplier_id"] == (
        "131468980"
    )


@pytest.mark.parametrize(
    "issue_date_block",
    [
        (
            "Дата на дан. събитие: 19.08.2026\n"
            "Дата на издаване: 19.08.2026"
        ),
        (
            "Дата на дан. събитие: 19.08.2026\n"
            "19.08.2026 Дата на издаване"
        ),
        (
            "Дата на издаване: 19.08.2026"
        ),
        (
            "Дата на издаване\n"
            "19.08.2026"
        ),
    ],
)
def test_a1_issue_date_variants(
    issue_date_block,
):
    values = extract_values(
        supplier_line="ЕИК:131468980",
        issue_date_block=issue_date_block,
        due_date_block=(
            "Краен срок на плащане: "
            "13.09.2026"
        ),
    )

    assert values["issue_date"] == (
        "19.08.2026"
    )


@pytest.mark.parametrize(
    "due_date_block",
    [
        (
            "Краен срок на плащане: "
            "13.09.2026"
        ),
        (
            "Краен срок на плащане:\n"
            "13.09.2026"
        ),
        (
            "Краен срок на плащане "
            "13.09.2026 г."
        ),
    ],
)
def test_a1_due_date_variants(
    due_date_block,
):
    values = extract_values(
        supplier_line="ЕИК:131468980",
        issue_date_block=(
            "Дата на дан. събитие: 19.08.2026\n"
            "Дата на издаване: 19.08.2026"
        ),
        due_date_block=due_date_block,
    )

    assert values["due_date"] == (
        "13.09.2026"
    )
