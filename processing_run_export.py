import csv
import io
import json
from collections.abc import Iterable
from typing import Any


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
