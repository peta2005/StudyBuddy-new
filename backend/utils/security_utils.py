import os
import re
import uuid

from werkzeug.utils import secure_filename

MAX_UPLOAD_BYTES = 50 * 1024 * 1024
PDF_MAGIC = b"%PDF"

UUID_RE = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$",
    re.IGNORECASE,
)


def validate_user_id(user_id: str) -> None:
    if not user_id or not UUID_RE.match(user_id):
        raise ValueError("Invalid user id")


def user_upload_dir(base_folder: str, user_id: str) -> str:
    validate_user_id(user_id)
    path = os.path.join(base_folder, user_id)
    os.makedirs(path, exist_ok=True)
    return path


def user_vector_dir(base_folder: str, user_id: str) -> str:
    validate_user_id(user_id)
    path = os.path.join(base_folder, user_id)
    os.makedirs(path, exist_ok=True)
    return path


def safe_pdf_filename(original_name: str) -> str:
    cleaned = secure_filename(original_name or "document.pdf")
    if not cleaned.lower().endswith(".pdf"):
        cleaned = f"{cleaned}.pdf" if cleaned else "document.pdf"
    unique = uuid.uuid4().hex[:12]
    stem = cleaned[:-4] if cleaned.lower().endswith(".pdf") else cleaned
    return f"{stem}_{unique}.pdf"


def validate_pdf_upload(file_storage, content_length: int | None) -> tuple[str, str]:
    if content_length is not None and content_length > MAX_UPLOAD_BYTES:
        raise ValueError("File exceeds the 50MB limit.")

    if not file_storage or not file_storage.filename:
        raise ValueError("No PDF file uploaded.")

    filename = safe_pdf_filename(file_storage.filename)
    if not filename.lower().endswith(".pdf"):
        raise ValueError("Only PDF files are allowed.")

    head = file_storage.stream.read(4)
    file_storage.stream.seek(0)
    if head != PDF_MAGIC:
        raise ValueError("Invalid PDF file.")

    return filename, secure_filename(file_storage.filename)
