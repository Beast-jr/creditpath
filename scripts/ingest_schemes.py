"""
scripts/ingest_schemes.py
One-time ingestion script. Re-run whenever scheme documents change.
Usage: python scripts/ingest_schemes.py
"""

from pathlib import Path
from core.rag.ingestor import ingest

SCHEMES_DIR = Path("data/schemes")
VECTORSTORE_PATH = Path("data/vectorstore")

if __name__ == "__main__":
    print("Ingesting scheme chunks into ChromaDB...")
    count = ingest(SCHEMES_DIR, VECTORSTORE_PATH)
    print(f"Done. {count} chunks ingested into 'scheme_passages' collection.")