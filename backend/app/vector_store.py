
from sentence_transformers import SentenceTransformer
import faiss
import numpy as np


# Load the embedding model
model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")


def create_chunks(text, chunk_size=500, overlap=80):
    """
    Divide document text into smaller overlapping chunks.
    """

    words = text.split()
    chunks = []

    start = 0

    while start < len(words):
        end = start + chunk_size

        chunk = " ".join(words[start:end])

        if chunk.strip():
            chunks.append(chunk)

        start += chunk_size - overlap

    return chunks


def build_vector_store(chunks):
    """
    Convert chunks into embeddings and store them in FAISS.
    """

    if not chunks:
        raise ValueError("No text chunks available.")

    embeddings = model.encode(
        chunks,
        convert_to_numpy=True,
        normalize_embeddings=True
    )

    embeddings = np.asarray(embeddings, dtype="float32")

    dimension = embeddings.shape[1]

    index = faiss.IndexFlatIP(dimension)
    index.add(embeddings)

    return index


def search_similar_chunks(question, index, chunks, top_k=4):
    """
    Find the most relevant chunks for a question.
    """

    question_embedding = model.encode(
        [question],
        convert_to_numpy=True,
        normalize_embeddings=True
    )

    question_embedding = np.asarray(
        question_embedding,
        dtype="float32"
    )

    number_of_results = min(top_k, len(chunks))

    scores, indices = index.search(
        question_embedding,
        number_of_results
    )

    results = []

    for score, idx in zip(scores[0], indices[0]):
        if idx != -1:
            results.append({
                "text": chunks[idx],
                "score": float(score)
            })

    return results
