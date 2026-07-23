"""
core/rag/ingestor.py
Embeds scheme chunks and stores them in ChromaDB.
Run once (or when schemes change) via scripts/ingest_schemes.py
"""

import chromadb
from chromadb.utils import embedding_functions
from pathlib import Path
from core.rag.chunker import load_all_chunks, SchemeChunk

COLLECTION_NAME = "scheme_passages"
EMBEDDING_MODEL = "all-MiniLM-L6-v2"  # same model your Day 15 pipeline uses


def get_collection(vectorstore_path: Path) -> chromadb.Collection:
    client = chromadb.PersistentClient(path=str(vectorstore_path))
    ef = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name=EMBEDDING_MODEL
    )
    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        embedding_function=ef,
        metadata={"hnsw:space": "cosine"},
    )
    return collection


def ingest(schemes_dir: Path, vectorstore_path: Path) -> int:
    """Chunk all schemes and upsert into ChromaDB. Returns count ingested."""
    chunks: list[SchemeChunk] = load_all_chunks(schemes_dir)
    collection = get_collection(vectorstore_path)

    collection.upsert(
        ids=[c.chunk_id for c in chunks],
        documents=[c.text for c in chunks],
        metadatas=[
            {
                "scheme_id": c.scheme_id,
                "scheme_name": c.scheme_name,
                "chunk_type": c.chunk_type,
                "official_url": c.official_url,
            }
            for c in chunks
        ],
    )
    return len(chunks)