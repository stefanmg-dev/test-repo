import csv
import io
import json
from datetime import datetime, timezone
from types import SimpleNamespace
from uuid import uuid4

from processing_run_export import (
    EXPORT_COLUMNS,
    stream_processing_runs_csv,
    stream_universal_invoice_feedback_jsonl,
)


NOW = datetime(2026, 9, 20, tzinfo=timezone.utc)


def make_run(overrides=None):
    values = {
        "id": uuid4(),
        "document_type": "invoice",
        "profile": "telecom_a1",
        "filename": "invoice.pdf",
        "processing_status": "review",
        "review_status": "corrected",
        "created_at": NOW,
        "completed_at": NOW,
        "reviewed_at": NOW,
        "configuration_hash": "abc123",
        "invoice_schema_version": "1",
        "reviewed_by_type": "user",
        "collections": {},
        "final_values": {
            "invoice_number": "ORIGINAL",
        },
        "corrected_values": {
            "invoice_number": "CORRECTED",
        },
    }

    if overrides:
        values.update(overrides)

    return SimpleNamespace(**values)


def parse_csv(processing_runs):
    content = "".join(
        stream_processing_runs_csv(processing_runs)
    )
    return list(csv.DictReader(io.StringIO(content)))


def test_exports_deterministic_columns_and_corrected_values():
    rows = parse_csv([make_run()])

    assert tuple(rows[0]) == EXPORT_COLUMNS
    assert rows[0]["effective_values_json"] == (
        '{"invoice_number":"CORRECTED"}'
    )
    assert rows[0]["configuration_hash"] == "abc123"


def test_rejected_review_has_no_effective_values():
    rows = parse_csv([
        make_run({
            "review_status": "rejected",
            "corrected_values": None,
        })
    ])

    assert rows[0]["effective_values_json"] == ""


def test_approved_review_uses_original_values():
    rows = parse_csv([
        make_run({
            "review_status": "approved",
            "corrected_values": None,
        })
    ])

    assert rows[0]["effective_values_json"] == (
        '{"invoice_number":"ORIGINAL"}'
    )


def test_neutralizes_spreadsheet_formula_prefixes():
    rows = parse_csv([
        make_run({"filename": "=DANGEROUS()"})
    ])

    assert rows[0]["filename"] == "'=DANGEROUS()"

def parse_feedback_jsonl(processing_runs):
    content = "".join(
        stream_universal_invoice_feedback_jsonl(processing_runs)
    )
    return [json.loads(line) for line in content.splitlines()]


def test_exports_deterministic_universal_invoice_feedback_jsonl():
    rows = parse_feedback_jsonl([make_run()])

    assert rows == [
        {
            "configuration_hash": "abc123",
            "invoice_schema_version": "1",
            "original_universal_invoice": {
                "abonat_number": None,
                "business_partner_number": None,
                "client_number": None,
                "consumption_items": [],
                "contract_account_number": None,
                "contract_number": None,
                "customer_address": None,
                "customer_name": None,
                "due_date": None,
                "installation_number": None,
                "invoice_number": "ORIGINAL",
                "issue_date": None,
                "metering_points": [],
                "meters": [],
                "schema_version": "1",
                "services": [],
                "supplier_id": None,
                "supplier_name": None,
                "total_amount": None,
                "total_consumption": None,
            },
            "processing_run_id": str(rows[0]["processing_run_id"]),
            "review_status": "corrected",
            "reviewed_at": NOW.isoformat(),
            "reviewed_by_type": "user",
            "reviewed_universal_invoice": {
                **rows[0]["original_universal_invoice"],
                "invoice_number": "CORRECTED",
            },
        }
    ]
    serialized = json.dumps(rows[0], ensure_ascii=False)
    assert "filename" not in serialized
    assert "raw_text" not in serialized
    assert "error" not in serialized
