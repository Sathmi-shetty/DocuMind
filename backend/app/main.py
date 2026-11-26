
import re
import sqlite3
import uuid
import os

from pathlib import Path
from fastapi import FastAPI, UploadFile, File, HTTPException, Header, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from app.database import create_tables, get_connection

from app.auth import (
    hash_password,
    verify_password,
    create_access_token,
    verify_access_token
)

from app.documents import (
    save_uploaded_pdf,
    extract_text_from_pdf,
    save_document_to_database
)

from app.summarizer import generate_summary

from app.vector_store import (
    create_chunks,
    build_vector_store,
    search_similar_chunks
)


app = FastAPI(
    title="DocuMind API",
    description="Backend API for DocuMind - AI Document Assistant",
    version="0.2.0"
)


# -------------------------------
# Authentication
# -------------------------------

def get_current_user(authorization: str = Header(None)):

    if not authorization:
        raise HTTPException(
            status_code=401,
            detail="Please log in first"
        )

    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail="Invalid authorization header"
        )

    token = authorization.split(" ", 1)[1]

    user_id = verify_access_token(token)

    if user_id is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token"
        )

    return user_id


# -------------------------------
# Startup
# -------------------------------

@app.on_event("startup")
def startup():
    create_tables()


# -------------------------------
# CORS Configuration
# -------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
        "http://localhost:5175",
        "http://127.0.0.1:5175",
        "http://localhost:5176",
        "http://127.0.0.1:5176",
        "http://localhost:5177",
        "http://127.0.0.1:5177"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)


# -------------------------------
# Request Models
# -------------------------------

class RegisterRequest(BaseModel):
    full_name: str = Field(min_length=2, max_length=100)
    email: str
    password: str = Field(min_length=8, max_length=128)


class LoginRequest(BaseModel):
    email: str
    password: str


class ChatRequest(BaseModel):
    document_id: int
    question: str = Field(min_length=1, max_length=1000)


# -------------------------------
# Home API
# -------------------------------

@app.get("/")
def read_root():
    return {
        "message": "Welcome to DocuMind API"
    }


# -------------------------------
# Health Check API
# -------------------------------

@app.get("/api/health")
def health_check():
    return {
        "status": "ok",
        "app": "DocuMind",
        "message": "Backend is running and connected!"
    }


# -------------------------------
# User Registration API
# -------------------------------

@app.post("/api/auth/register")
def register_user(user: RegisterRequest):

    full_name = user.full_name.strip()
    email = user.email.strip().lower()

    if (
        len(full_name) < 2
        or "@" not in email
        or "." not in email.split("@")[-1]
    ):
        raise HTTPException(
            status_code=400,
            detail="Please provide a valid name and email address"
        )

    connection = get_connection()

    try:
        existing_user = connection.execute(
            "SELECT id FROM users WHERE email = ?",
            (email,)
        ).fetchone()

        if existing_user:
            raise HTTPException(
                status_code=409,
                detail="Email is already registered"
            )

        hashed_password = hash_password(user.password)

        cursor = connection.execute(
            """
            INSERT INTO users (full_name, email, hashed_password)
            VALUES (?, ?, ?)
            """,
            (full_name, email, hashed_password)
        )

        connection.commit()

        return {
            "message": "Registration successful!",
            "user_id": cursor.lastrowid,
            "full_name": full_name,
            "email": email
        }

    except sqlite3.IntegrityError:
        raise HTTPException(
            status_code=409,
            detail="Email is already registered"
        )

    finally:
        connection.close()


# -------------------------------
# User Login API
# -------------------------------

@app.post("/api/auth/login")
def login_user(user: LoginRequest):

    email = user.email.strip().lower()

    connection = get_connection()

    try:
        existing_user = connection.execute(
            "SELECT * FROM users WHERE email = ?",
            (email,)
        ).fetchone()

        if not existing_user or not verify_password(
            user.password,
            existing_user["hashed_password"]
        ):
            raise HTTPException(
                status_code=401,
                detail="Incorrect email or password"
            )

        access_token = create_access_token(existing_user["id"])

        return {
            "message": "Login successful!",
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "id": existing_user["id"],
                "full_name": existing_user["full_name"],
                "email": existing_user["email"]
            }
        }

    finally:
        connection.close()


# -------------------------------
# PDF Upload API
# -------------------------------

@app.post("/api/documents/upload")
async def upload_document(
    file: UploadFile = File(...),
    current_user: int = Depends(get_current_user)
):

    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are allowed"
        )

    file_content = await file.read()

    if not file_content.startswith(b"%PDF"):
        raise HTTPException(
            status_code=400,
            detail="Invalid PDF file"
        )

    if len(file_content) > 10 * 1024 * 1024:
        raise HTTPException(
            status_code=400,
            detail="PDF must be smaller than 10 MB"
        )

    filename = f"{uuid.uuid4()}.pdf"

    file_path = save_uploaded_pdf(file_content, filename)

    pages = extract_text_from_pdf(file_path)

    extracted_text = "\n\n".join(
        page["text"] for page in pages
    )

    save_document_to_database(
        current_user,
        filename,
        file.filename,
        len(pages),
        extracted_text
    )

    return {
        "message": "PDF uploaded and saved successfully",
        "filename": filename,
        "total_pages": len(pages),
        "pages": pages
    }


# -------------------------------
# Get Uploaded Documents API
# -------------------------------

@app.get("/api/documents")
def get_documents(
    current_user: int = Depends(get_current_user)
):

    connection = get_connection()

    try:
        documents = connection.execute(
            """
            SELECT id, filename, original_filename,
                   total_pages, uploaded_at
            FROM documents
            WHERE user_id = ?
            ORDER BY uploaded_at DESC
            """,
            (current_user,)
        ).fetchall()

        return {
            "documents": [dict(document) for document in documents]
        }

    finally:
        connection.close()


# -------------------------------
# PDF Summary API
# -------------------------------

@app.get("/api/documents/{document_id}/summary")
def summarize_document(
    document_id: int,
    current_user: int = Depends(get_current_user)
):

    connection = get_connection()

    try:
        document = connection.execute(
            """
            SELECT id, original_filename, extracted_text
            FROM documents
            WHERE id = ? AND user_id = ?
            """,
            (document_id, current_user)
        ).fetchone()

        if not document:
            raise HTTPException(
                status_code=404,
                detail="Document not found"
            )

        summary = generate_summary(document["extracted_text"])

        return {
            "document_id": document["id"],
            "filename": document["original_filename"],
            "summary": summary
        }

    finally:
        connection.close()


# -------------------------------
# Semantic Search Chat API
# -------------------------------

@app.post("/api/documents/chat")
def chat_with_document(
    request: ChatRequest,
    current_user: int = Depends(get_current_user)
):

    connection = get_connection()

    try:
        document = connection.execute(
            """
            SELECT id, filename, original_filename
            FROM documents
            WHERE id = ? AND user_id = ?
            """,
            (request.document_id, current_user)
        ).fetchone()

        if not document:
            raise HTTPException(
                status_code=404,
                detail="Document not found"
            )

        pdf_path = (
            Path(__file__).resolve().parent.parent
            / "uploads"
            / document["filename"]
        )

        if not pdf_path.exists():
            raise HTTPException(
                status_code=404,
                detail="Stored PDF file not found. Please upload again."
            )

        # Extract text from PDF pages
        pages = extract_text_from_pdf(str(pdf_path))

        full_text = "\n\n".join(
            page["text"] for page in pages
        )

        if not full_text.strip():
            raise HTTPException(
                status_code=400,
                detail="This PDF does not contain readable text."
            )

        # Divide document into smaller chunks
        chunks = create_chunks(full_text)

        # Create FAISS vector index
        index = build_vector_store(chunks)

        # Retrieve relevant chunks
        results = search_similar_chunks(
            request.question,
            index,
            chunks,
            top_k=4
        )

        if not results:
            answer = "No relevant information was found in this document."

        else:
            answer = "\n\n".join(
                result["text"] for result in results
            )

        # Remove presentation heading and name/USN
        answer = re.sub(
            r"PRESENTED BY.*?(?=geometric dual|$)",
            "",
            answer,
            flags=re.IGNORECASE | re.DOTALL
        )

        # Remove repeated placeholder text
        answer = re.sub(
            r"Write your topic here",
            "",
            answer,
            flags=re.IGNORECASE
        )

        # Clean extra spaces
        answer = re.sub(r"\s+", " ", answer).strip()

        # Keep answer short
        words = answer.split()

        if len(words) > 70:
            answer = " ".join(words[:70]) + "..."

        return {
            "document_id": document["id"],
            "filename": document["original_filename"],
            "question": request.question,
            "answer": answer,
            "retrieved_chunks": len(results),
            "sources": results
        }

    finally:
        connection.close()


# -------------------------------
# Delete PDF API
# -------------------------------

@app.delete("/api/documents/{document_id}")
def delete_document(
    document_id: int,
    current_user: int = Depends(get_current_user)
):

    connection = get_connection()

    try:
        document = connection.execute(
            """
            SELECT filename
            FROM documents
            WHERE id = ? AND user_id = ?
            """,
            (document_id, current_user)
        ).fetchone()

        if not document:
            raise HTTPException(
                status_code=404,
                detail="Document not found"
            )

        pdf_path = (
            Path(__file__).resolve().parent.parent
            / "uploads"
            / document["filename"]
        )

        connection.execute(
            """
            DELETE FROM documents
            WHERE id = ? AND user_id = ?
            """,
            (document_id, current_user)
        )

        connection.commit()

        if pdf_path.exists():
            os.remove(pdf_path)

        return {
            "message": "Document deleted successfully"
        }

    finally:
        connection.close()


# -------------------------------
# Download PDF API
# -------------------------------

@app.get("/api/documents/{document_id}/download")
def download_document(
    document_id: int,
    current_user: int = Depends(get_current_user)
):

    connection = get_connection()

    try:
        document = connection.execute(
            """
            SELECT filename, original_filename
            FROM documents
            WHERE id = ? AND user_id = ?
            """,
            (document_id, current_user)
        ).fetchone()

        if not document:
            raise HTTPException(
                status_code=404,
                detail="Document not found"
            )

        pdf_path = (
            Path(__file__).resolve().parent.parent
            / "uploads"
            / document["filename"]
        )

        if not pdf_path.exists():
            raise HTTPException(
                status_code=404,
                detail="PDF file not found"
            )

        return FileResponse(
            path=pdf_path,
            media_type="application/pdf",
            filename=document["original_filename"]
        )

    finally:
        connection.close()
