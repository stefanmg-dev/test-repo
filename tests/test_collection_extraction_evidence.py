from collection_extractor import (
    extract_collection_item,
    extract_collection_item_with_evidence,
)
from collection_pipeline import (
    extract_collections_from_schemas_with_evidence,
)


FIELDS = [
    {
        "name": "amount",
        "type": "regex_list",
        "rules": [r"Missing: ([0-9,]+)", r"Amount: ([0-9,]+)"],
        "occurrence": "first",
        "validation": [{"type": "decimal"}],
    },
    {
        "name": "reference",
        "type": "regex",
        "rule": r"Reference: ([A-Z0-9]+)",
        "occurrence": "last",
        "validation": [],
    },
]


def test_collection_item_evidence_explains_match_and_failure():
    item, evidence = extract_collection_item_with_evidence(
        item_text="Amount: 12,34",
        fields=FIELDS,
    )
    assert item == {"amount": "12.34", "reference": None}
    assert evidence["amount"] == {
        "method": "regex_list",
        "matched": True,
        "normalized": True,
        "occurrence": "first",
        "rule_index": 1,
    }
    assert evidence["reference"]["failure_reason"] == (
        "pattern_not_matched"
    )
    assert "value" not in evidence["amount"]
    assert "pattern" not in evidence["amount"]


def test_existing_collection_item_contract_is_preserved():
    assert extract_collection_item(
        item_text="Amount: 12,34",
        fields=FIELDS,
    ) == {"amount": "12.34", "reference": None}


def test_collection_pipeline_aligns_items_and_evidence():
    collections, evidence = extract_collections_from_schemas_with_evidence(
        raw_text="Item Amount: 1,20\nItem Amount: 2,30",
        collections={
            "items": {
                "start_pattern": r"^Item",
                "fields": FIELDS[:1],
            },
            "empty": {"fields": []},
        },
    )
    assert collections == {
        "items": [{"amount": "1.20"}, {"amount": "2.30"}],
        "empty": [],
    }
    assert len(evidence["items"]) == 2
    assert evidence["empty"] == []
