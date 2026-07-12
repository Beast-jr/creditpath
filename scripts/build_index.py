"""Build the ChromaDB vector index from scheme JSON documents.

One-time script. Safe to re-run (idempotent by default).
Use --rebuild to wipe and rebuild from scratch.

Usage:
    python -m scripts.build_index
    python -m scripts.build_index --rebuild
"""

import argparse
import json
import logging
import sys
from pathlib import Path

import chromadb
from sentence_transformers import SentenceTransformer

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)

SCHEMES_DIR = Path(__file__).resolve().parent.parent / "data" / "schemes"
CHROMA_PATH = Path(__file__).resolve().parent.parent / "data" / "embeddings" / "chroma"
COLLECTION_NAME = "scheme_kb"
MODEL_NAME = "all-MiniLM-L6-v2"


def _load_schemes() -> list[dict]:
    schemes = []
    for path in sorted(SCHEMES_DIR.glob("*.json")):
        data = json.loads(path.read_text())
        schemes.append(data)
    return schemes


def _scheme_to_metadata(scheme: dict) -> dict:
    """Flatten scheme fields into ChromaDB-compatible metadata (strings only)."""
    return {
        "scheme_id": scheme["scheme_id"],
        "name": scheme["name"],
        "administered_by": scheme["administered_by"],
        "scheme_type": scheme["scheme_type"],
        "target_segments": "|".join(scheme["target_segments"]),
        "loan_range_min": str(scheme["loan_range_min"]),
        "loan_range_max": str(scheme["loan_range_max"]),
        "interest_rate_min": str(scheme["interest_rate_min"]),
        "interest_rate_max": str(scheme["interest_rate_max"]),
        "collateral_required": str(scheme["collateral_required"]),
        "eligibility_vintage_months_min": str(scheme["eligibility_vintage_months_min"]),
        "eligibility_gst_required": str(scheme["eligibility_gst_required"]),
        "eligibility_sectors_included": "|".join(scheme["eligibility_sectors_included"]),
        "eligibility_sectors_excluded": "|".join(scheme["eligibility_sectors_excluded"]),
        "eligibility_geographic_restriction": scheme["eligibility_geographic_restriction"],
        "retrieval_text": scheme["retrieval_text"],
        "official_url": scheme["official_url"],
        "last_verified_date": scheme["last_verified_date"],
    }


def build(rebuild: bool = False) -> None:
    schemes = _load_schemes()
    logger.info("Loaded %d scheme documents", len(schemes))

    CHROMA_PATH.mkdir(parents=True, exist_ok=True)
    client = chromadb.PersistentClient(path=str(CHROMA_PATH))

    if rebuild:
        try:
            client.delete_collection(COLLECTION_NAME)
            logger.info("Deleted existing collection '%s'", COLLECTION_NAME)
        except Exception:
            pass

    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "l2"},
    )

    existing_ids = set(collection.get()["ids"])
    to_add = [s for s in schemes if s["scheme_id"] not in existing_ids]

    if not to_add:
        logger.info("Index already up to date — %d documents, nothing to add", len(existing_ids))
        return

    logger.info("Embedding %d new documents with %s…", len(to_add), MODEL_NAME)
    model = SentenceTransformer(MODEL_NAME)

    texts = [s["retrieval_text"] for s in to_add]
    embeddings = model.encode(texts, show_progress_bar=True).tolist()

    collection.add(
        ids=[s["scheme_id"] for s in to_add],
        embeddings=embeddings,
        metadatas=[_scheme_to_metadata(s) for s in to_add],
        documents=texts,
    )

    logger.info(
        "Index built: %d documents in collection '%s' at %s",
        collection.count(),
        COLLECTION_NAME,
        CHROMA_PATH,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Build ChromaDB scheme index")
    parser.add_argument("--rebuild", action="store_true", help="Wipe and rebuild from scratch")
    args = parser.parse_args()
    build(rebuild=args.rebuild)
    return 0


if __name__ == "__main__":
    sys.exit(main())