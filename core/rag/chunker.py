"""
core/rag/chunker.py
Converts scheme JSON documents into passage-level chunks for RAG retrieval.
Each scheme produces two or three chunks: eligibility summary, description,
and (where available) a required-documents checklist.
"""

import json
from pathlib import Path
from dataclasses import dataclass


@dataclass
class SchemeChunk:
    chunk_id: str          # e.g. "cgtmse_eligibility"
    scheme_id: str
    scheme_name: str
    chunk_type: str        # "eligibility" | "description" | "documents"
    text: str
    official_url: str


def _format_eligibility_chunk(doc: dict) -> str:
    """Build a readable eligibility passage from structured fields."""
    lines = []

    name = doc["name"]
    lines.append(f"Scheme: {name}")
    lines.append(f"Administered by: {doc.get('administered_by', 'N/A')}")
    lines.append(f"Type: {doc.get('scheme_type', 'N/A')}")

    loan_min = doc.get("loan_range_min", 0)
    loan_max = doc.get("loan_range_max", 0)
    lines.append(f"Loan range: Rs {loan_min:,} to Rs {loan_max:,}")

    rate_min = doc.get("interest_rate_min")
    rate_max = doc.get("interest_rate_max")
    if rate_min is not None and rate_max is not None:
        lines.append(f"Interest rate: {rate_min}% to {rate_max}%")

    collateral = doc.get("collateral_required", True)
    lines.append(f"Collateral required: {'Yes' if collateral else 'No'}")

    vintage = doc.get("eligibility_vintage_months_min", 0)
    lines.append(f"Minimum business vintage: {vintage} months")

    gst = doc.get("eligibility_gst_required", False)
    lines.append(f"GST registration required: {'Yes' if gst else 'No'}")

    segments = doc.get("target_segments", [])
    if segments:
        lines.append(f"Target segments: {', '.join(segments)}")

    included = doc.get("eligibility_sectors_included", [])
    excluded = doc.get("eligibility_sectors_excluded", [])
    if included:
        lines.append(f"Eligible sectors: {', '.join(included)}")
    if excluded:
        lines.append(f"Excluded sectors: {', '.join(excluded)}")

    geo = doc.get("eligibility_geographic_restriction", "")
    if geo:
        lines.append(f"Geographic restriction: {geo}")

    return "\n".join(lines)


def _format_documents_chunk(scheme_name: str, documents: list[str]) -> str:
    """Build a readable required-documents passage."""
    header = f"Documents required to apply for {scheme_name}:"
    body = "\n".join(f"- {d}" for d in documents)
    return f"{header}\n{body}"


def chunk_scheme(doc: dict) -> list[SchemeChunk]:
    """Produce two or three chunks from one scheme document."""
    scheme_id = doc["scheme_id"]
    scheme_name = doc["name"]
    url = doc.get("official_url", "")

    eligibility_text = _format_eligibility_chunk(doc)
    description_text = doc.get("retrieval_text", "").strip()

    chunks = [
        SchemeChunk(
            chunk_id=f"{scheme_id}_eligibility",
            scheme_id=scheme_id,
            scheme_name=scheme_name,
            chunk_type="eligibility",
            text=eligibility_text,
            official_url=url,
        ),
        SchemeChunk(
            chunk_id=f"{scheme_id}_description",
            scheme_id=scheme_id,
            scheme_name=scheme_name,
            chunk_type="description",
            text=description_text,
            official_url=url,
        ),
    ]

    # Documents chunk only exists for schemes that have been enriched.
    documents = doc.get("documents_required")
    if documents:
        chunks.append(
            SchemeChunk(
                chunk_id=f"{scheme_id}_documents",
                scheme_id=scheme_id,
                scheme_name=scheme_name,
                chunk_type="documents",
                text=_format_documents_chunk(scheme_name, documents),
                official_url=url,
            )
        )

    return chunks


def load_all_chunks(schemes_dir: Path) -> list[SchemeChunk]:
    """Load and chunk all scheme JSON files in the given directory."""
    chunks = []
    for path in sorted(schemes_dir.glob("*.json")):
        with open(path, encoding="utf-8") as f:
            doc = json.load(f)
        chunks.extend(chunk_scheme(doc))
    return chunks