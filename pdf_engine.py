import fitz  # PyMuPDF
from pdf2image import convert_from_path
from pdf2image.exceptions import PDFPageCountError
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

class InvalidPdfError(ValueError):
    """Raised when PDF content cannot be parsed."""


def pdf_to_images(pdf_path: str):
    try:
        pages = convert_from_path(pdf_path)
    except PDFPageCountError as exc:
        raise InvalidPdfError(
            "Invalid or corrupted PDF file"
        ) from exc
    image_paths = []

    for page in pages:
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
        page.save(tmp.name, "PNG")
        image_paths.append(tmp.name)

    return image_paths
