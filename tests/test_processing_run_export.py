import csv
import io
from datetime import datetime, timezone
from types import SimpleNamespace
from uuid import uuid4

from processing_run_export import (
    EXPORT_COLUMNS,
    stream_processing_runs_csv,
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
