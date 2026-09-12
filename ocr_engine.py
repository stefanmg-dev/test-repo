import os
import tempfile

import easyocr
import numpy as np
from PIL import Image, ImageOps

from input_quality import evaluate_image_quality
from pdf_engine import (
    extract_pdf_text,
    is_native_pdf,
    pdf_to_images,
)


reader = easyocr.Reader(
    ["bg", "en"],
    gpu=False,
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


def run_ocr(image_path: str) -> str:
    result = run_ocr_with_quality(
        image_path
    )

    return result["text"]


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


async def extract_text(file) -> str:
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
        raise ValueError(
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
            if is_native_pdf(temp_file_path):
                native_text = extract_pdf_text(
                    temp_file_path
                )

                generated_image_paths = (
                    pdf_to_images(
                        temp_file_path
                    )
                )

                first_page_ocr = ""

                if generated_image_paths:
                    first_page_ocr = run_ocr(
                        generated_image_paths[0]
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

                return "\n\n".join(text_parts)

            generated_image_paths = pdf_to_images(
                temp_file_path
            )

            ocr_pages = []

            for image_path in generated_image_paths:
                page_text = run_ocr(image_path)

                if page_text.strip():
                    ocr_pages.append(
                        page_text.strip()
                    )

            return "\n\n".join(ocr_pages)

        return run_ocr(
            temp_file_path
        ).strip()

    finally:
        remove_file(temp_file_path)

        for image_path in generated_image_paths:
            remove_file(image_path)
