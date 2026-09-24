import os
import tempfile
from dataclasses import dataclass

import pymupdf
from fastapi import UploadFile
from PIL import Image, UnidentifiedImageError

from app_settings import AppSettings, get_settings


UPLOAD_READ_CHUNK_SIZE = 1024 * 1024
SUPPORTED_EXTENSIONS = {".pdf", ".jpg", ".jpeg", ".png"}


class DocumentInputError(ValueError):
    """Base error for invalid uploaded document input."""


class UnsupportedFileTypeError(DocumentInputError):
    """Raised when uploaded content has an unsupported type."""


class InvalidDocumentInputError(DocumentInputError):
    """Raised when uploaded document content is invalid."""


class PayloadTooLargeError(DocumentInputError):
    """Raised when uploaded content exceeds its configured limit."""


@dataclass(frozen=True)
class ValidatedUpload:
    path: str
    extension: str
    size_bytes: int


def validate_filename(filename: str, settings: AppSettings) -> str:
    if len(filename) > settings.max_filename_length:
        raise InvalidDocumentInputError(
            "Filename exceeds the configured length limit"
        )

    extension = os.path.splitext(filename)[1].lower()
    if extension not in SUPPORTED_EXTENSIONS:
        raise UnsupportedFileTypeError(
            "Unsupported file type: "
            f"{extension or 'unknown'}"
        )
    return extension


def validate_signature(path: str, extension: str) -> None:
    with open(path, "rb") as uploaded_file:
        signature = uploaded_file.read(16)

    if extension == ".pdf":
        valid = signature.startswith(b"%PDF-")
    elif extension == ".png":
        valid = signature.startswith(b"\x89PNG\r\n\x1a\n")
    else:
        valid = signature.startswith(b"\xff\xd8\xff")

    if not valid:
        raise InvalidDocumentInputError(
            "File content does not match its extension"
        )


def validate_pdf(path: str, settings: AppSettings) -> None:
    try:
        with pymupdf.open(path) as document:
            page_count = document.page_count
    except Exception as exc:
        raise InvalidDocumentInputError(
            "Invalid or corrupted PDF file"
        ) from exc

    if page_count <= 0:
        raise InvalidDocumentInputError(
            "PDF must contain at least one page"
        )
    if page_count > settings.max_pdf_pages:
        raise InvalidDocumentInputError(
            "PDF exceeds the configured page limit"
        )


def validate_image(path: str, settings: AppSettings) -> None:
    try:
        with Image.open(path) as image:
            width, height = image.size
            image.verify()
    except (UnidentifiedImageError, OSError) as exc:
        raise InvalidDocumentInputError(
            "Invalid or corrupted image file"
        ) from exc

    if (
        width > settings.max_image_width
        or height > settings.max_image_height
        or width * height > settings.max_image_pixels
    ):
        raise InvalidDocumentInputError(
            "Image exceeds the configured dimension limit"
        )


async def persist_validated_upload(
    file: UploadFile,
    *,
    settings: AppSettings | None = None,
) -> ValidatedUpload:
    settings = settings or get_settings()
    filename = file.filename or ""
    extension = validate_filename(filename, settings)
    path = None
    size_bytes = 0

    try:
        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=extension,
        ) as temporary_file:
            path = temporary_file.name
            while True:
                chunk = await file.read(UPLOAD_READ_CHUNK_SIZE)
                if not chunk:
                    break
                size_bytes += len(chunk)
                if size_bytes > settings.max_upload_size_bytes:
                    raise PayloadTooLargeError(
                        "Uploaded file exceeds the configured size limit"
                    )
                temporary_file.write(chunk)

        if size_bytes == 0:
            raise InvalidDocumentInputError(
                "Uploaded file is empty"
            )

        validate_signature(path, extension)
        if extension == ".pdf":
            validate_pdf(path, settings)
        else:
            validate_image(path, settings)

        return ValidatedUpload(
            path=path,
            extension=extension,
            size_bytes=size_bytes,
        )
    except Exception:
        if path and os.path.exists(path):
            os.remove(path)
        raise
