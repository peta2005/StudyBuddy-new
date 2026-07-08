import fitz  # PyMuPDF
import pytesseract
from PIL import Image
import io

import sys
if sys.platform.startswith("win"):
    pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"


# Minimum characters on a page before we consider it "has text".
# Pages below this threshold will also get OCR applied.
_TEXT_THRESHOLD = 50


def _ocr_page(page: fitz.Page) -> str:
    """
    Render a PDF page to an image and run Tesseract OCR on it.
    Returns the OCR-extracted text string.
    """
    # Render at 2x zoom for better OCR accuracy
    matrix = fitz.Matrix(2.0, 2.0)
    pix = page.get_pixmap(matrix=matrix, colorspace=fitz.csRGB)
    img_bytes = pix.tobytes("png")
    img = Image.open(io.BytesIO(img_bytes))
    text = pytesseract.image_to_string(img, lang="eng")
    return text.strip()


def extract_text_per_page(pdf_path: str) -> list[dict]:
    pages = []
    ocr_available = _check_tesseract()

    doc = fitz.open(pdf_path)

    # First-pass fast character count
    total_chars = 0
    fast_texts = []
    for page in doc:
        txt = page.get_text("text").strip()
        fast_texts.append(txt)
        total_chars += len(txt)

    # If the document has a decent amount of text, skip OCR entirely.
    # Otherwise, treat it as a scanned/image PDF.
    num_pages = len(doc)
    is_scanned = ocr_available and (num_pages > 0 and (total_chars / num_pages) < 100)

    for i, page in enumerate(doc):
        text = fast_texts[i]

        # Step 2: OCR fallback if text is sparse AND it is a scanned PDF
        if is_scanned and len(text) < _TEXT_THRESHOLD:
            try:
                ocr_text = _ocr_page(page)
                # Merge: prefer OCR if it found more content
                if len(ocr_text) > len(text):
                    text = ocr_text
                elif ocr_text:
                    text = text + "\n" + ocr_text
            except Exception as e:
                print(f"[OCR] Page {i + 1} OCR failed: {e}")

        pages.append({"page": i + 1, "text": text or ""})

    doc.close()
    return pages


def _check_tesseract() -> bool:
    """Check if Tesseract is installed and accessible."""
    try:
        pytesseract.get_tesseract_version()
        return True
    except Exception:
        print(
            "[OCR] Tesseract not found — falling back to text-only extraction.\n"
            "      To enable OCR, install Tesseract from:\n"
            "      https://github.com/UB-Mannheim/tesseract/wiki"
        )
        return False
