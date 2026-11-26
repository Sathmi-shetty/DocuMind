
# DocuMind – AI-Powered Document Assistant

DocuMind is a full-stack web application that helps users upload PDF documents, view summaries, and ask questions about their documents using semantic search.

## Features

- User registration and login
- Secure authentication using JWT
- PDF upload and text extraction
- Automatic document summarization
- Semantic search using Sentence Transformers and FAISS
- Ask questions about uploaded PDF documents
- View, download, and delete uploaded documents
- User-specific document management

## Technologies Used

**Frontend:** React, Vite, JavaScript

**Backend:** Python, FastAPI

**Database:** SQLite

**AI and Search:** Sentence Transformers, FAISS

**PDF Processing:** PyMuPDF

## How It Works

1. Users register or log in.
2. Users upload PDF documents.
3. DocuMind extracts text from the PDF.
4. The application generates a document summary.
5. Semantic search retrieves relevant content based on user questions.
6. The relevant document content is displayed as the answer.

## Project Structure

```text
DocuMind/
├── backend/
│   └── app/
│       ├── main.py
│       ├── auth.py
│       ├── database.py
│       ├── documents.py
│       ├── summarizer.py
│       └── vector_store.py
│
├── frontend/
│
└── README.md
```

## How to Run

### Backend

```bash
cd backend
```

Activate the Python virtual environment and install the dependencies listed in `requirements.txt`.

Start the server:

```bash
uvicorn app.main:app --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

## Project Objective

The objective of DocuMind is to make document reading and information retrieval easier by combining PDF processing, summarization, and semantic search in one application.

## Developed By

Sathmi Shetty

Computer Science and Engineering
