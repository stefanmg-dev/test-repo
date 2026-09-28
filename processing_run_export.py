import csv
import io
import json
from collections.abc import Iterable
from typing import Any

from invoice_mapper import map_extraction_to_universal_invoice


EXPORT_COLUMNS = (
    "processing_run_id",
    "document_type",
    "profile",
    "filename",
    "processing_status",
    "review_status",
    "created_at",
    "completed_at",
    "reviewed_at",
    "configuration_hash",
    "effective_values_json",
)


def effective_values(processing_run) -> dict[str, Any] | None:
    if processing_run.review_status == "rejected":
        return None
    if processing_run.review_status == "corrected":
        return processing_run.corrected_values
    return processing_run.final_values


def safe_csv_value(value: Any) -> str:
    if value is None:
        return ""

    text = str(value)
    dangerous_prefixes = ("=", "+", "-", "@", "\t", "\r")

    if text.startswith(dangerous_prefixes):
        return "'" + text

    return text


def serialize_json(value: Any) -> str:
    if value is None:
        return ""

    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )


def export_row(processing_run) -> dict[str, str]:
    return {
        "processing_run_id": str(processing_run.id),
        "document_type": safe_csv_value(
            processing_run.document_type
        ),
        "profile": safe_csv_value(processing_run.profile),
        "filename": safe_csv_value(processing_run.filename),
        "processing_status": safe_csv_value(
            processing_run.processing_status
        ),
        "review_status": safe_csv_value(
            processing_run.review_status
        ),
        "created_at": processing_run.created_at.isoformat(),
        "completed_at": (
            processing_run.completed_at.isoformat()
            if processing_run.completed_at
            else ""
        ),
        "reviewed_at": (
            processing_run.reviewed_at.isoformat()
            if processing_run.reviewed_at
            else ""
        ),
        "configuration_hash": safe_csv_value(
            processing_run.configuration_hash
        ),
        "effective_values_json": serialize_json(
            effective_values(processing_run)
        ),
    }


def universal_invoice_feedback_record(processing_run):
    original_invoice = map_extraction_to_universal_invoice(
        document_type=processing_run.document_type,
        final_values=processing_run.final_values or {},
        collections=processing_run.collections or {},
    )
    reviewed_values = (
        processing_run.corrected_values
        if processing_run.review_status == "corrected"
        else processing_run.final_values
    )
    reviewed_invoice = map_extraction_to_universal_invoice(
        document_type=processing_run.document_type,
        final_values=reviewed_values or {},
        collections=processing_run.collections or {},
    )
    return {
        "processing_run_id": str(processing_run.id),
        "configuration_hash": processing_run.configuration_hash,
        "invoice_schema_version": (
            processing_run.invoice_schema_version
        ),
        "review_status": processing_run.review_status,
        "reviewed_at": (
            processing_run.reviewed_at.isoformat()
            if processing_run.reviewed_at
            else None
        ),
        "reviewed_by_type": processing_run.reviewed_by_type,
        "original_universal_invoice": (
            original_invoice.model_dump(mode="json")
            if original_invoice is not None
            else None
        ),
        "reviewed_universal_invoice": (
            reviewed_invoice.model_dump(mode="json")
            if reviewed_invoice is not None
            else None
        ),
    }


def stream_universal_invoice_feedback_jsonl(
    processing_runs: Iterable,
):
    for processing_run in processing_runs:
        yield json.dumps(
            universal_invoice_feedback_record(processing_run),
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ) + "\n"


def stream_processing_runs_csv(
    processing_runs: Iterable,
):
    buffer = io.StringIO()
    writer = csv.DictWriter(
        buffer,
        fieldnames=EXPORT_COLUMNS,
        extrasaction="raise",
        lineterminator="\n",
    )

    writer.writeheader()
    yield buffer.getvalue()
    buffer.seek(0)
    buffer.truncate(0)

    for processing_run in processing_runs:
        writer.writerow(export_row(processing_run))
        yield buffer.getvalue()
        buffer.seek(0)
        buffer.truncate(0)
