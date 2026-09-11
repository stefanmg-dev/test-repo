import fitz  # PyMuPDF
from pdf2image import convert_from_path
import tempfile

def is_native_pdf(pdf_path: str) -> bool:
    doc = fitz.open(pdf_path)
    first_page_text = doc[0].get_text()
    return bool(first_page_text.strip())

def extract_pdf_text(pdf_path: str) -> str:
    doc = fitz.open(pdf_path)
    full_text = []

    for page in doc:
        text = page.get_text()
        if text:
            full_text.append(text)

    return "\n".join(full_text)

def pdf_to_images(pdf_path: str):
    pages = convert_from_path(pdf_path)
    image_paths = []

    for page in pages:
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
        page.save(tmp.name, "PNG")
        image_paths.append(tmp.name)

    return image_paths
