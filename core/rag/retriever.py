"""
core/rag/retriever.py
Retrieves relevant scheme chunks from ChromaDB for a user question.
"""

import chromadb
from chromadb.utils import embedding_functions
from pathlib import Path
from dataclasses import dataclass

COLLECTION_NAME = "scheme_passages"
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
DEFAULT_TOP_K = 5


@dataclass
class RetrievedChunk:
    chunk_id: str
    scheme_id: str
    scheme_name: str
    chunk_type: str
    text: str
    official_url: str
    distance: float


def get_retriever(vectorstore_path: Path):
    client = chromadb.PersistentClient(path=str(vectorstore_path))
    ef = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name=EMBEDDING_MODEL
    )
    collection = client.get_collection(
        name=COLLECTION_NAME,
        embedding_function=ef,
    )
    return collection


def retrieve(question: str, collection, top_k: int = DEFAULT_TOP_K) -> list[RetrievedChunk]:
    """Embed question and return top_k most similar scheme chunks."""
    results = collection.query(
        query_texts=[question],
        n_results=top_k,
    )

    chunks = []
    for chunk_id, doc, meta, distance in zip(
        results["ids"][0],
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0],
    ):
        chunks.append(RetrievedChunk(
            chunk_id=chunk_id,
            scheme_id=meta["scheme_id"],
            scheme_name=meta["scheme_name"],
            chunk_type=meta["chunk_type"],
            text=doc,
            official_url=meta["official_url"],
            distance=distance,
        ))
    return chunks