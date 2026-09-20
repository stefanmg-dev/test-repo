import asyncio
from io import BytesIO

import pytest
from fastapi import UploadFile

import ocr_engine


def make_upload(
    filename,
    content=b"fixture-content",
):
    return UploadFile(
        file=BytesIO(content),
        filename=filename,
    )


def extract(upload):
    return asyncio.run(
        ocr_engine.extract_document_input(upload)
    )


def accepted_image_quality(image_format):
    return {
        "status": "accepted",
        "requires_review": False,
        "input": {
            "format": image_format,
            "width": 1652,
            "height": 2338,
            "short_edge": 1652,
            "long_edge": 2338,
            "pixel_count": 3862376,
            "mode": "RGB",
            "dpi": None,
        },
        "warnings": [],
    }


def test_native_pdf_uses_native_text_and_first_page_ocr(
    monkeypatch,
):
    monkeypatch.setattr(
        ocr_engine,
        "pdf_to_images",
        lambda path: [
            "/tmp/native-page-1.png",
            "/tmp/native-page-2.png",
        ],
    )
    monkeypatch.setattr(
        ocr_engine,
        "is_native_pdf",
        lambda path: True,
    )
    monkeypatch.setattr(
        ocr_engine,
        "extract_pdf_text",
        lambda path: "Native PDF text",
    )

    ocr_calls = []

    def fake_run_ocr_with_quality(path):
        ocr_calls.append(path)

        return {
            "text": "First page OCR text",
            "quality": accepted_image_quality(
                "PNG"
            ),
        }

    monkeypatch.setattr(
        ocr_engine,
        "run_ocr_with_quality",
        fake_run_ocr_with_quality,
    )
    monkeypatch.setattr(
        ocr_engine,
        "remove_file",
        lambda path: None,
    )

    result = extract(
        make_upload("invoice.pdf")
    )

    assert result == {
        "text": (
            "Native PDF text\n\n"
            "First page OCR text"
        ),
        "quality": {
            "status": "accepted",
            "requires_review": False,
            "input": {
                "format": "PDF",
                "source": "native_pdf",
                "page_count": 2,
            },
            "warnings": [],
        },
    }

    assert ocr_calls == [
        "/tmp/native-page-1.png",
    ]


def test_scanned_pdf_ocr_processes_every_page(
    monkeypatch,
):
    page_paths = [
        "/tmp/scanned-page-1.png",
        "/tmp/scanned-page-2.png",
    ]

    monkeypatch.setattr(
        ocr_engine,
        "pdf_to_images",
        lambda path: page_paths,
    )
    monkeypatch.setattr(
        ocr_engine,
        "is_native_pdf",
        lambda path: False,
    )

    def fake_run_ocr_with_quality(path):
        page_number = page_paths.index(path) + 1

        return {
            "text": f"Scanned page {page_number}",
            "quality": accepted_image_quality(
                "PNG"
            ),
        }

    monkeypatch.setattr(
        ocr_engine,
        "run_ocr_with_quality",
        fake_run_ocr_with_quality,
    )
    monkeypatch.setattr(
        ocr_engine,
        "remove_file",
        lambda path: None,
    )

    result = extract(
        make_upload("scan.pdf")
    )

    assert result["text"] == (
        "Scanned page 1\n\nScanned page 2"
    )

    assert result["quality"] == {
        "status": "accepted",
        "requires_review": False,
        "input": {
            "format": "PDF",
            "source": "scanned_pdf",
            "page_count": 2,
            "pages": [
                accepted_image_quality(
                    "PNG"
                )["input"],
                accepted_image_quality(
                    "PNG"
                )["input"],
            ],
        },
        "warnings": [],
    }


@pytest.mark.parametrize(
    (
        "filename",
        "expected_format",
    ),
    [
        (
            "invoice.png",
            "PNG",
        ),
        (
            "invoice.jpg",
            "JPEG",
        ),
        (
            "invoice.jpeg",
            "JPEG",
        ),
    ],
)
def test_supported_image_routes_to_ocr(
    monkeypatch,
    filename,
    expected_format,
):
    calls = []

    def fake_run_ocr_with_quality(path):
        calls.append(path)

        return {
            "text": "Image OCR text",
            "quality": accepted_image_quality(
                expected_format
            ),
        }

    monkeypatch.setattr(
        ocr_engine,
        "run_ocr_with_quality",
        fake_run_ocr_with_quality,
    )
    monkeypatch.setattr(
        ocr_engine,
        "remove_file",
        lambda path: None,
    )

    result = extract(
        make_upload(filename)
    )

    assert result["text"] == "Image OCR text"
    assert result["quality"]["input"][
        "format"
    ] == expected_format
    assert len(calls) == 1


@pytest.mark.parametrize(
    "filename",
    [
        "invoice.heic",
        "invoice.tiff",
        "invoice.webp",
        "invoice.bmp",
        "invoice",
    ],
)
def test_unsupported_input_format_is_rejected(
    filename,
):
    with pytest.raises(
        ValueError,
        match="Unsupported file type",
    ):
        extract(
            make_upload(filename)
        )
