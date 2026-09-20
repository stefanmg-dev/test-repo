import asyncio
import os
from pathlib import Path

import pytest
from fastapi import UploadFile

from config_store import load_config
from extraction_orchestrator import apply_rules
from ocr_engine import extract_document_input


FIXTURE_DIRECTORY = os.getenv(
    "A1_REAL_JPEG_DIR"
)

VARIANTS = [
    (
        "Factura_A1_0826_JPEG150_Q85.jpg",
        "review",
        True,
    ),
    (
        "Factura_A1_0826_JPEG200_Q85.jpeg",
        "accepted",
        False,
    ),
    (
        "Factura_A1_0826_JPEG300_Q85.jpg",
        "accepted",
        False,
    ),
    (
        "Factura_A1_0826_JPEG300_Q60.jpg",
        "accepted",
        False,
    ),
    (
        "Factura_A1_0826_JPEG300_EXIF_ROTATED.jpg",
        "accepted",
        False,
    ),
]


async def extract_fixture(path):
    with path.open("rb") as source:
        upload = UploadFile(
            file=source,
            filename=path.name,
        )

        return await extract_document_input(
            upload
        )


def test_a1_real_jpeg_variants_end_to_end():
    if not FIXTURE_DIRECTORY:
        pytest.skip(
            "A1_REAL_JPEG_DIR is not configured"
        )

    fixture_directory = Path(
        FIXTURE_DIRECTORY
    )

    config = load_config()

    for (
        filename,
        expected_quality_status,
        expected_requires_review,
    ) in VARIANTS:
        fixture_path = (
            fixture_directory / filename
        )

        assert fixture_path.is_file(), (
            f"JPEG fixture was not found: "
            f"{fixture_path}"
        )

        document_input = asyncio.run(
            extract_fixture(fixture_path)
        )

        quality = document_input["quality"]

        assert quality["input"]["format"] == (
            "JPEG"
        )
        assert quality["status"] == (
            expected_quality_status
        )
        assert quality["requires_review"] is (
            expected_requires_review
        )

        values = apply_rules(
            document_type="invoice",
            config=config,
            raw_text=document_input["text"],
            llm_values={},
        )

        assert values["supplier_id"] == (
            "131468980"
        )
        assert values["invoice_number"] == (
            "0726592493"
        )
        assert values["issue_date"] == (
            "19.08.2026"
        )
        assert values["due_date"] == (
            "13.09.2026"
        )
        assert values["total_amount"] == (
            "67.96"
        )

        assert values[
            "contract_number"
        ] in {
            "M5781970",
            "М5781970",
        }
