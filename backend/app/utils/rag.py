"""
RAG pipeline using FAISS + sentence-transformers (100% free, local).
"""
import os
import numpy as np

_embedder = None
_index = None
_documents = []
_initialized = False


def _get_embedder():
    """Lazy-load sentence-transformers model."""
    global _embedder
    if _embedder is not None:
        return _embedder
    try:
        from sentence_transformers import SentenceTransformer
        _embedder = SentenceTransformer("all-MiniLM-L6-v2")
        return _embedder
    except Exception as e:
        print(f"[RAG] Embedder init error: {e}")
        return None


def init_rag():
    """Initialize or load FAISS index."""
    global _index, _documents, _initialized
    if _initialized:
        return

    try:
        import faiss
        _index = faiss.IndexFlatL2(384)  # all-MiniLM-L6-v2 dimension
        _documents = []
        _initialized = True
        print("[RAG] Initialized empty FAISS index")
    except Exception as e:
        print(f"[RAG] FAISS init error: {e}")


def add_to_index(text: str, metadata: dict = None):
    """Add a document to the FAISS index."""
    global _index, _documents
    init_rag()

    embedder = _get_embedder()
    if embedder is None or _index is None:
        return

    try:
        embedding = embedder.encode([text])
        _index.add(np.array(embedding, dtype=np.float32))
        _documents.append({"text": text, "metadata": metadata or {}})
    except Exception as e:
        print(f"[RAG] Add error: {e}")


def search(query: str, top_k: int = 3) -> list:
    """Search the FAISS index for relevant documents."""
    global _index, _documents
    init_rag()

    embedder = _get_embedder()
    if embedder is None or _index is None or _index.ntotal == 0:
        return []

    try:
        query_embedding = embedder.encode([query])
        distances, indices = _index.search(np.array(query_embedding, dtype=np.float32), min(top_k, _index.ntotal))

        results = []
        for i, idx in enumerate(indices[0]):
            if idx < len(_documents) and idx >= 0:
                results.append({
                    "text": _documents[idx]["text"],
                    "metadata": _documents[idx]["metadata"],
                    "score": float(distances[0][i]),
                })
        return results
    except Exception as e:
        print(f"[RAG] Search error: {e}")
        return []


def get_context_for_query(query: str, top_k: int = 3) -> str:
    """Get relevant context string for RAG."""
    results = search(query, top_k)
    if not results:
        return ""

    context_parts = []
    for r in results:
        context_parts.append(r["text"])

    return "\n\n---\n\n".join(context_parts)
