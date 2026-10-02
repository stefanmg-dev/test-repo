from extraction_orchestrator import (
    apply_rules,
    apply_rules_with_evidence,
    extract_document_data,
)


def build_config():
    return {
        "invoice": {
            "common_fields": [
                {"name": "constant_value", "type": "constant", "value": " Supplier ", "validation": []},
                {"name": "llm_value", "type": "llm", "validation": []},
                {"name": "regex_value", "type": "regex", "rule": r"Number: ([0-9]+)", "occurrence": "first", "validation": []},
                {"name": "list_value", "type": "regex_list", "rules": [r"Missing: ([0-9]+)", r"Total: ([0-9,]+)"], "occurrence": "last", "validation": [{"type": "decimal"}]},
                {"name": "nearby_value", "type": "nearby", "anchor": "Amount", "pattern": r"([0-9,]+)", "occurrence": "first", "direction": "after", "window_size": 20, "validation": [{"type": "decimal"}]},
                {"name": "missing_nearby", "type": "nearby", "anchor": "Absent", "pattern": r"([0-9]+)", "validation": []},
            ],
            "collections": {},
        }
    }


def test_rule_evidence_is_safe_and_explains_outcomes():
    values, evidence = apply_rules_with_evidence(
        document_type="invoice",
        config=build_config(),
        raw_text="Number: 10 Total: 12,34 Amount 56,78",
        llm_values={"llm_value": "model"},
    )
    assert values["list_value"] == "12.34"
    assert values["nearby_value"] == "56.78"
    assert evidence["constant_value"] == {"method": "constant", "matched": True, "normalized": False}
    assert evidence["regex_value"]["occurrence"] == "first"
    assert evidence["list_value"]["rule_index"] == 1
    assert evidence["list_value"]["normalized"] is True
    assert evidence["nearby_value"]["anchor_found"] is True
    assert evidence["missing_nearby"]["failure_reason"] == "anchor_not_found"
    assert "value" not in evidence["regex_value"]
    assert "pattern" not in evidence["regex_value"]
    assert "anchor" not in evidence["missing_nearby"]


def test_apply_rules_preserves_existing_value_only_contract():
    result = apply_rules(
        document_type="invoice",
        config=build_config(),
        raw_text="Number: 10 Total: 12,34 Amount 56,78",
        llm_values={"llm_value": "model"},
    )
    assert result["list_value"] == "12.34"


def test_document_engine_returns_field_evidence():
    result = extract_document_data(
        document_type="invoice",
        config=build_config(),
        raw_text="Number: 10 Total: 12,34 Amount 56,78",
        llm_values={"llm_value": "model"},
    )
    assert result["field_evidence"]["regex_value"]["matched"] is True
