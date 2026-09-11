import os
import tempfile

import easyocr

from pdf_engine import (
    is_native_pdf,
    extract_pdf_text,
    pdf_to_images
)


reader = easyocr.Reader(
    ["bg", "en"],
    gpu=False
)


def run_ocr(image_path: str) -> str:
    results = reader.readtext(
        image_path,
        detail=0,
        paragraph=True
    )

    return "\n".join(results)


def remove_file(path: str | None) -> None:
    if not path:
        return

    try:
        if os.path.exists(path):
            os.remove(path)
    except OSError:
        pass


async def extract_text(file) -> str:
    filename = file.filename or ""
    extension = os.path.splitext(filename)[1].lower()

    if extension not in {".pdf", ".jpg", ".jpeg", ".png"}:
        raise ValueError(
            f"Unsupported file type: {extension or 'unknown'}"
        )

    temp_file_path = None
    generated_image_paths = []

    try:
        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=extension
        ) as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_file_path = temp_file.name

        if extension == ".pdf":
            if is_native_pdf(temp_file_path):
                native_text = extract_pdf_text(temp_file_path)

                generated_image_paths = pdf_to_images(
                    temp_file_path
                )

                first_page_ocr = ""

                if generated_image_paths:
                    first_page_ocr = run_ocr(
                        generated_image_paths[0]
                    )

                text_parts = []

                if native_text.strip():
                    text_parts.append(native_text.strip())

                if first_page_ocr.strip():
                    text_parts.append(first_page_ocr.strip())

                return "\n\n".join(text_parts)

            generated_image_paths = pdf_to_images(
                temp_file_path
            )

            ocr_pages = []

            for image_path in generated_image_paths:
                page_text = run_ocr(image_path)

                if page_text.strip():
                    ocr_pages.append(page_text.strip())

            return "\n\n".join(ocr_pages)

        return run_ocr(temp_file_path).strip()

    finally:
        remove_file(temp_file_path)

        for image_path in generated_image_paths:
            remove_file(image_path)