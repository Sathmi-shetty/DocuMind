import fitz
from pathlib import Path

UPLOAD_DIR = Path(__file__).resolve().parent.parent / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)


def save_uploaded_pdf(file, filename):
    file_path = UPLOAD_DIR / filename

    with open(file_path, "wb") as buffer:
        buffer.write(file)

    return str(file_path)


def extract_text_from_pdf(file_path: str):
    document = fitz.open(file_path)

    pages = []

    for page_number, page in enumerate(document, start=1):
        pages.append({
            "page": page_number,
            "text": page.get_text()
        })

    document.close()

    return pages
    import sqlite3
from app.database import get_connection


def save_document_to_database(
    user_id,
    filename,
    original_filename,
    total_pages,
    extracted_text
):
    connection = get_connection()

    try:
        connection.execute(
            """
            INSERT INTO documents
            (user_id, filename, original_filename, total_pages, extracted_text)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                user_id,
                filename,
                original_filename,
                total_pages,
                extracted_text
            )
        )

        connection.commit()

    finally:
        connection.close()