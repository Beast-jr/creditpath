"""ChromaDB-backed semantic retriever for financing schemes.

Queries the persistent vector index built by scripts/build_index.py.
Never rebuilds the index at runtime — index must be built separately.
"""

import logging
from pathlib import Path
from typing import List

import chromadb
from sentence_transformers import SentenceTransformer

from core.schema import SchemeDocument, SchemeMatch

logger = logging.getLogger(__name__)

CHROMA_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "embeddings" / "chroma"
COLLECTION_NAME = "scheme_kb"
MODEL_NAME = "all-MiniLM-L6-v2"


class SchemeRetriever:
    """Semantic retriever backed by ChromaDB + all-MiniLM-L6-v2.

    The embedding model is loaded once on __init__ and reused for all queries.
    retrieve() only returns schemes whose IDs are in candidate_ids — this
    enforces that the constraint filter always runs before retrieval.
    """

    def __init__(self):
        logger.info("Loading embedding model: %s", MODEL_NAME)
        self._model = SentenceTransformer(MODEL_NAME)

        client = chromadb.PersistentClient(path=str(CHROMA_PATH))
        self._collection = client.get_collection(COLLECTION_NAME)
        logger.info(
            "Connected to ChromaDB collection '%s' (%d documents)",
            COLLECTION_NAME,
            self._collection.count(),
        )

    def retrieve(
        self,
        query: str,
        candidate_ids: List[str],
        k: int,
    ) -> List[SchemeMatch]:
        """Return up to k schemes ranked by semantic similarity to query.

        Only schemes whose scheme_id is in candidate_ids are considered.
        If candidate_ids is empty, returns an empty list immediately.

        Args:
            query: Free-text description of the business need.
            candidate_ids: scheme_ids that passed the constraint filter.
            k: Maximum number of results to return.

        Returns:
            List of SchemeMatch ordered by descending similarity (best first).
        """
        if not candidate_ids:
            logger.info("retrieve() called with empty candidate_ids — returning []")
            return []

        query_embedding = self._model.encode(query).tolist()

        results = self._collection.query(
            query_embeddings=[query_embedding],
            n_results=min(k, len(candidate_ids)),
            where={"scheme_id": {"$in": candidate_ids}},
            include=["metadatas", "distances"],
        )

        matches = []
        metadatas = results["metadatas"][0]
        distances = results["distances"][0]

        for meta, distance in zip(metadatas, distances):
            # ChromaDB returns L2 distance; convert to 0-1 similarity score
            similarity = 1.0 / (1.0 + distance)

            scheme = SchemeDocument(
                scheme_id=meta["scheme_id"],
                name=meta["name"],
                administered_by=meta["administered_by"],
                scheme_type=meta["scheme_type"],
                target_segments=meta["target_segments"].split("|"),
                loan_range_min=float(meta["loan_range_min"]),
                loan_range_max=float(meta["loan_range_max"]),
                interest_rate_min=float(meta["interest_rate_min"]),
                interest_rate_max=float(meta["interest_rate_max"]),
                collateral_required=meta["collateral_required"] == "True",
                eligibility_vintage_months_min=int(meta["eligibility_vintage_months_min"]),
                eligibility_gst_required=meta["eligibility_gst_required"] == "True",
                eligibility_sectors_included=meta["eligibility_sectors_included"].split("|") if meta["eligibility_sectors_included"] else [],
                eligibility_sectors_excluded=meta["eligibility_sectors_excluded"].split("|") if meta["eligibility_sectors_excluded"] else [],
                eligibility_geographic_restriction=meta["eligibility_geographic_restriction"],
                retrieval_text=meta["retrieval_text"],
                official_url=meta["official_url"],
                last_verified_date=meta["last_verified_date"],
            )

            matches.append(SchemeMatch(
                scheme=scheme,
                match_score=round(similarity, 4),
                eligibility_explanation="",  # filled by ranker in Day 16
            ))

        logger.info(
            "retrieve() returned %d/%d candidates for query: %.60s…",
            len(matches),
            len(candidate_ids),
            query,
        )
        return matches