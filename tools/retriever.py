# tools/retriever.py
import os
import json
import chromadb
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

DOCS_PATH = "knowledge_base/company_docs.txt"
CHROMA_PATH = "memory/chroma_store"

groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# ── Simple keyword search (no embedding model needed) ──────────
def _simple_search(query: str, chunks: list, n_results: int = 2) -> list:
    """
    Scores each chunk by how many query words appear in it.
    No internet, no model download needed.
    """
    query_words = query.lower().split()
    scores = []

    for chunk in chunks:
        chunk_lower = chunk.lower()
        score = sum(1 for word in query_words if word in chunk_lower)
        scores.append((score, chunk))

    # Sort by score descending, return top n
    scores.sort(key=lambda x: x[0], reverse=True)
    return [chunk for score, chunk in scores[:n_results] if score > 0]


def _load_chunks() -> list:
    """Load and split company docs into chunks."""
    if not os.path.exists(DOCS_PATH):
        return []
    with open(DOCS_PATH, "r") as f:
        content = f.read()
    return [chunk.strip() for chunk in content.split("\n\n") if chunk.strip()]


def load_documents():
    """Verify docs exist and are readable."""
    chunks = _load_chunks()
    if chunks:
        print(f"✅ Knowledge base ready — {len(chunks)} chunks loaded.")
    else:
        print(f"⚠️ No docs found at {DOCS_PATH}")


def retrieve(query: str, n_results: int = 2) -> str:
    """
    Search knowledge base for relevant info using keyword matching.
    Then use Groq to summarize the results naturally.
    """
    chunks = _load_chunks()

    if not chunks:
        return "No knowledge base available."

    # Find relevant chunks
    relevant = _simple_search(query, chunks, n_results)

    if not relevant:
        return "No relevant information found in knowledge base."

    # Use Groq to generate a clean answer from the chunks
    context = "\n\n".join(relevant)

    prompt = f"""
You are a helpful assistant. Answer the query using ONLY the context below.
Be concise and direct.

Context:
{context}

Query: {query}
"""
    response = groq_client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}]
    )

    return response.choices[0].message.content.strip()