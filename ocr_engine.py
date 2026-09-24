import os
import tempfile

import easyocr
import numpy as np
from PIL import Image, ImageOps, UnidentifiedImageError

from input_quality import evaluate_image_quality
from pdf_engine import (
    InvalidPdfError,
    extract_pdf_text,
    is_native_pdf,
    pdf_to_images,
)


easyocr_model_directory = os.getenv(
    "EASYOCR_MODEL_STORAGE_DIRECTORY"
)
easyocr_user_network_directory = os.getenv(
    "EASYOCR_USER_NETWORK_DIRECTORY"
)
easyocr_download_enabled = os.getenv(
    "EASYOCR_DOWNLOAD_ENABLED",
    "true",
).lower() in {"1", "true", "yes"}

reader = easyocr.Reader(
    ["bg", "en"],
    gpu=False,
    model_storage_directory=easyocr_model_directory,
    user_network_directory=(
        easyocr_user_network_directory
    ),
    download_enabled=easyocr_download_enabled,
)


def inspect_image_quality(
    image_path: str,
) -> dict:
    with Image.open(image_path) as image:
        normalized_image = ImageOps.exif_transpose(
            image
        )

        width, height = normalized_image.size

        return evaluate_image_quality(
            image_format=image.format,
            width=width,
            height=height,
            mode=normalized_image.mode,
            dpi=image.info.get("dpi"),
        )


def load_rgb_image(
    image_path: str,
) -> np.ndarray:
    with Image.open(image_path) as image:
        normalized_image = ImageOps.exif_transpose(
            image
        )

        has_transparency = (
            normalized_image.mode in {
                "RGBA",
                "LA",
            }
            or (
                normalized_image.mode == "P"
                and "transparency"
                in normalized_image.info
            )
        )

        if has_transparency:
            rgba_image = normalized_image.convert(
                "RGBA"
            )

            white_background = Image.new(
                "RGBA",
                rgba_image.size,
                (255, 255, 255, 255),
            )

            normalized_image = Image.alpha_composite(
                white_background,
                rgba_image,
            ).convert("RGB")

        else:
            normalized_image = (
                normalized_image.convert("RGB")
            )

        return np.asarray(
            normalized_image,
            dtype=np.uint8,
        ).copy()


def run_ocr_with_quality(
    image_path: str,
) -> dict:
    quality = inspect_image_quality(
        image_path
    )

    image = load_rgb_image(
        image_path
    )

    results = reader.readtext(
        image,
        detail=0,
        paragraph=True,
    )

    return {
        "text": "\n".join(results),
        "quality": quality,
    }


def run_ocr(
    image_path: str,
) -> str:
    result = run_ocr_with_quality(
        image_path
    )

    return result["text"]


def build_native_pdf_quality(
    page_count: int,
) -> dict:
    return {
        "status": "accepted",
        "requires_review": False,
        "input": {
            "format": "PDF",
            "source": "native_pdf",
            "page_count": page_count,
        },
        "warnings": [],
    }


def build_scanned_pdf_quality(
    page_qualities: list[dict],
) -> dict:
    requires_review = any(
        quality.get("requires_review") is True
        for quality in page_qualities
    )

    warnings = []

    if requires_review:
        warnings.append(
            {
                "code": "low_page_resolution",
                "message": (
                    "One or more PDF pages may have "
                    "insufficient resolution for "
                    "reliable OCR"
                ),
            }
        )

    return {
        "status": (
            "review"
            if requires_review
            else "accepted"
        ),
        "requires_review": requires_review,
        "input": {
            "format": "PDF",
            "source": "scanned_pdf",
            "page_count": len(page_qualities),
            "pages": [
                quality["input"]
                for quality in page_qualities
            ],
        },
        "warnings": warnings,
    }


def remove_file(
    path: str | None,
) -> None:
    if not path:
        return

    try:
        if os.path.exists(path):
            os.remove(path)

    except OSError:
        pass


class DocumentInputError(ValueError):
    """Base error for invalid uploaded document input."""


class UnsupportedFileTypeError(DocumentInputError):
    """Raised when the uploaded document format is not supported."""


class InvalidDocumentInputError(DocumentInputError):
    """Raised when uploaded document content cannot be processed."""


async def extract_document_input(file) -> dict:
    filename = file.filename or ""

    extension = os.path.splitext(
        filename
    )[1].lower()

    supported_extensions = {
        ".pdf",
        ".jpg",
        ".jpeg",
        ".png",
    }

    if extension not in supported_extensions:
        raise UnsupportedFileTypeError(
            "Unsupported file type: "
            f"{extension or 'unknown'}"
        )

    temp_file_path = None
    generated_image_paths = []

    try:
        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=extension,
        ) as temp_file:
            content = await file.read()

            temp_file.write(content)

            temp_file_path = temp_file.name

        if extension == ".pdf":
            try:
                generated_image_paths = pdf_to_images(
                    temp_file_path
                )
            except InvalidPdfError as exc:
                raise InvalidDocumentInputError(
                    str(exc)
                ) from exc

            if is_native_pdf(temp_file_path):
                native_text = extract_pdf_text(
                    temp_file_path
                )

                first_page_ocr = ""

                if generated_image_paths:
                    first_page_result = (
                        run_ocr_with_quality(
                            generated_image_paths[0]
                        )
                    )

                    first_page_ocr = (
                        first_page_result["text"]
                    )

                text_parts = []

                if native_text.strip():
                    text_parts.append(
                        native_text.strip()
                    )

                if first_page_ocr.strip():
                    text_parts.append(
                        first_page_ocr.strip()
                    )

                return {
                    "text": "\n\n".join(
                        text_parts
                    ),
                    "quality": (
                        build_native_pdf_quality(
                            len(
                                generated_image_paths
                            )
                        )
                    ),
                }

            ocr_pages = []
            page_qualities = []

            for image_path in generated_image_paths:
                page_result = run_ocr_with_quality(
                    image_path
                )

                page_text = page_result["text"]

                page_qualities.append(
                    page_result["quality"]
                )

                if page_text.strip():
                    ocr_pages.append(
                        page_text.strip()
                    )

            return {
                "text": "\n\n".join(
                    ocr_pages
                ),
                "quality": (
                    build_scanned_pdf_quality(
                        page_qualities
                    )
                ),
            }

        try:
            image_result = run_ocr_with_quality(
                temp_file_path
            )
        except UnidentifiedImageError as exc:
            raise InvalidDocumentInputError(
                "Invalid or corrupted image file"
            ) from exc

        return {
            "text": image_result["text"].strip(),
            "quality": image_result["quality"],
        }

    finally:
        remove_file(temp_file_path)

        for image_path in generated_image_paths:
            remove_file(image_path)


async def extract_text(file) -> str:
    result = await extract_document_input(file)

    return result["text"]