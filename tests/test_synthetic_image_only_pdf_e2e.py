import asyncio
from io import BytesIO
from pathlib import Path

import pymupdf
from fastapi import UploadFile
from PIL import Image, ImageDraw

import ocr_engine


def build_page_image(label: str) -> bytes:
    image = Image.new("RGB", (1200, 1600), "white")
    draw = ImageDraw.Draw(image)
    draw.rectangle((80, 80, 1120, 1520), outline="black", width=4)
    draw.text((140, 180), label, fill="black")

    buffer = BytesIO()
    image.save(buffer, "PNG")
    return buffer.getvalue()


def build_image_only_pdf() -> bytes:
    document = pymupdf.open()

    for label in ("Synthetic page one", "Synthetic page two"):
        page = document.new_page(width=600, height=800)
        page.insert_image(
            pymupdf.Rect(0, 0, 600, 800),
            stream=build_page_image(label),
        )

    content = document.tobytes()
    document.close()
    return content


def make_upload() -> UploadFile:
    return UploadFile(
        file=BytesIO(build_image_only_pdf()),
        filename="synthetic-image-only.pdf",
    )


def test_image_only_multi_page_pdf_uses_real_rendering_and_cleans_up(
    monkeypatch,
):
    upload_paths = []
    rendered_paths = []
    ocr_paths = []

    real_persist = ocr_engine.persist_validated_upload
    real_pdf_to_images = ocr_engine.pdf_to_images

    async def capture_upload(file):
        validated = await real_persist(file)
        upload_paths.append(validated.path)
        return validated

    def capture_rendering(pdf_path):
        paths = real_pdf_to_images(pdf_path)
        rendered_paths.extend(paths)
        return paths

    def fake_ocr(path):
        ocr_paths.append(path)
        page_number = len(ocr_paths)
        quality = ocr_engine.inspect_image_quality(path)
        return {
            "text": f"Synthetic OCR page {page_number}",
            "quality": quality,
        }

    monkeypatch.setattr(
        ocr_engine,
        "persist_validated_upload",
        capture_upload,
    )
    monkeypatch.setattr(
        ocr_engine,
        "pdf_to_images",
        capture_rendering,
    )
    monkeypatch.setattr(
        ocr_engine,
        "run_ocr_with_quality",
        fake_ocr,
    )

    result = asyncio.run(
        ocr_engine.extract_document_input(make_upload())
    )

    assert result["text"] == (
        "Synthetic OCR page 1\n\nSynthetic OCR page 2"
    )
    assert result["quality"]["input"]["format"] == "PDF"
    assert result["quality"]["input"]["source"] == "scanned_pdf"
    assert result["quality"]["input"]["page_count"] == 2
    assert len(result["quality"]["input"]["pages"]) == 2

    assert len(upload_paths) == 1
    assert len(rendered_paths) == 2
    assert ocr_paths == rendered_paths

    for temporary_path in upload_paths + rendered_paths:
        assert not Path(temporary_path).exists()
