from extraction_orchestrator import apply_rules


def build_config():
    return {
        "synthetic_invoice": {
            "fields": [
                {
                    "name": "amount_after_anchor",
                    "type": "nearby",
                    "anchor": "Amount due",
                    "pattern": r"([0-9]+,[0-9]{2})",
                    "direction": "after",
                    "window_size": 40,
                    "occurrence": "first",
                    "validation": [{"type": "decimal"}],
                },
                {
                    "name": "reference_before_anchor",
                    "type": "nearby",
                    "anchor": "Reference marker",
                    "pattern": r"REF-([0-9]{4})",
                    "direction": "before",
                    "window_size": 30,
                    "occurrence": "last",
                    "validation": [],
                },
                {
                    "name": "last_code_near_anchor",
                    "type": "nearby",
                    "anchor": "Codes",
                    "pattern": r"CODE-([A-Z])",
                    "direction": "both",
                    "window_size": 45,
                    "occurrence": "last",
                    "validation": [],
                },
            ]
        }
    }


def test_nearby_rules_respect_direction_window_occurrence_and_decimal_normalization():
    raw_text = (
        "REF-0001 distant-prefix-data "
        "REF-2048 Reference marker "
        "Amount due   123,45 trailing 999,99 "
        "CODE-A Codes CODE-B"
    )

    result = apply_rules(
        document_type="synthetic_invoice",
        config=build_config(),
        raw_text=raw_text,
        llm_values={},
    )

    assert result == {
        "amount_after_anchor": "123.45",
        "reference_before_anchor": "2048",
        "last_code_near_anchor": "B",
    }


def test_nearby_rule_returns_none_when_anchor_is_missing():
    result = apply_rules(
        document_type="synthetic_invoice",
        config=build_config(),
        raw_text="No configured anchors are present",
        llm_values={},
    )

    assert result == {
        "amount_after_anchor": None,
        "reference_before_anchor": None,
        "last_code_near_anchor": None,
    }
