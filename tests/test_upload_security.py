from io import BytesIO

import pymupdf
import pytest
from fastapi import UploadFile
from PIL import Image

from app_settings import AppSettings
from upload_security import (
    InvalidDocumentInputError,
    PayloadTooLargeError,
    UnsupportedFileTypeError,
    persist_validated_upload,
)


def settings(**overrides):
    values = {
        "DATABASE_URL": "postgresql+psycopg://u:p@localhost/db",
        **overrides,
    }
    return AppSettings(_env_file=None, **values)


def upload(filename, content):
    return UploadFile(file=BytesIO(content), filename=filename)


@pytest.mark.anyio
async def test_rejects_oversized_upload_before_full_buffering():
    with pytest.raises(PayloadTooLargeError):
        await persist_validated_upload(
            upload("invoice.pdf", b"%PDF-" + b"x" * 2048),
            settings=settings(MAX_UPLOAD_SIZE_BYTES=1024),
        )


@pytest.mark.anyio
async def test_rejects_extension_signature_mismatch():
    with pytest.raises(
        InvalidDocumentInputError,
        match="does not match",
    ):
        await persist_validated_upload(
            upload("invoice.pdf", b"not-a-pdf"),
            settings=settings(),
        )


@pytest.mark.anyio
async def test_rejects_pdf_above_page_limit():
    document = pymupdf.open()
    document.new_page()
    document.new_page()
    content = document.tobytes()
    document.close()

    with pytest.raises(
        InvalidDocumentInputError,
        match="page limit",
    ):
        await persist_validated_upload(
            upload("invoice.pdf", content),
            settings=settings(MAX_PDF_PAGES=1),
        )


@pytest.mark.anyio
async def test_rejects_image_above_pixel_limit():
    buffer = BytesIO()
    Image.new("RGB", (20, 20), "white").save(buffer, "PNG")

    with pytest.raises(
        InvalidDocumentInputError,
        match="dimension limit",
    ):
        await persist_validated_upload(
            upload("invoice.png", buffer.getvalue()),
            settings=settings(MAX_IMAGE_PIXELS=100),
        )
