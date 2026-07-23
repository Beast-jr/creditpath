"""Unit tests for core/rag/chunker.py — pure functions, no API calls."""

import json
import pytest
from pathlib import Path
from core.rag.chunker import (
    chunk_scheme,
    load_all_chunks,
    _format_eligibility_chunk,
    _format_documents_chunk,
    SchemeChunk,
)


@pytest.fixture
def minimal_scheme():
    return {
        "scheme_id": "test_scheme",
        "name": "Test Scheme",
        "administered_by": "Test Ministry",
        "scheme_type": "term_loan",
        "target_segments": ["micro", "small"],
        "loan_range_min": 50000,
        "loan_range_max": 1000000,
        "interest_rate_min": 8.0,
        "interest_rate_max": 12.0,
        "collateral_required": False,
        "eligibility_vintage_months_min": 12,
        "eligibility_gst_required": True,
        "eligibility_sectors_included": ["manufacturing"],
        "eligibility_sectors_excluded": ["agriculture"],
        "eligibility_geographic_restriction": "",
        "retrieval_text": "A test scheme for unit testing.",
        "official_url": "https://example.gov.in/",
        "last_verified_date": "2026-07-10",
    }


class TestChunkScheme:

    def test_unenriched_scheme_produces_two_chunks(self, minimal_scheme):
        chunks = chunk_scheme(minimal_scheme)
        assert len(chunks) == 2
        assert [c.chunk_type for c in chunks] == ["eligibility", "description"]

    def test_enriched_scheme_produces_three_chunks(self, minimal_scheme):
        minimal_scheme["documents_required"] = ["PAN Card", "Udyam Certificate"]
        chunks = chunk_scheme(minimal_scheme)
        assert len(chunks) == 3
        assert chunks[2].chunk_type == "documents"

    def test_empty_documents_list_produces_no_documents_chunk(self, minimal_scheme):
        minimal_scheme["documents_required"] = []
        chunks = chunk_scheme(minimal_scheme)
        assert len(chunks) == 2

    def test_chunk_ids_are_unique_and_prefixed(self, minimal_scheme):
        minimal_scheme["documents_required"] = ["PAN Card"]
        chunks = chunk_scheme(minimal_scheme)
        ids = [c.chunk_id for c in chunks]
        assert ids == [
            "test_scheme_eligibility",
            "test_scheme_description",
            "test_scheme_documents",
        ]
        assert len(set(ids)) == len(ids)

    def test_metadata_propagates_to_every_chunk(self, minimal_scheme):
        minimal_scheme["documents_required"] = ["PAN Card"]
        for chunk in chunk_scheme(minimal_scheme):
            assert chunk.scheme_id == "test_scheme"
            assert chunk.scheme_name == "Test Scheme"
            assert chunk.official_url == "https://example.gov.in/"

    def test_description_chunk_uses_retrieval_text(self, minimal_scheme):
        chunks = chunk_scheme(minimal_scheme)
        assert chunks[1].text == "A test scheme for unit testing."


class TestEligibilityFormatting:

    def test_includes_core_fields(self, minimal_scheme):
        text = _format_eligibility_chunk(minimal_scheme)
        assert "Test Scheme" in text
        assert "Rs 50,000 to Rs 1,000,000" in text
        assert "8.0% to 12.0%" in text

    def test_collateral_and_gst_render_as_yes_no(self, minimal_scheme):
        text = _format_eligibility_chunk(minimal_scheme)
        assert "Collateral required: No" in text
        assert "GST registration required: Yes" in text

    def test_empty_geographic_restriction_is_omitted(self, minimal_scheme):
        text = _format_eligibility_chunk(minimal_scheme)
        assert "Geographic restriction" not in text

    def test_geographic_restriction_included_when_present(self, minimal_scheme):
        minimal_scheme["eligibility_geographic_restriction"] = "Karnataka"
        text = _format_eligibility_chunk(minimal_scheme)
        assert "Geographic restriction: Karnataka" in text

    def test_empty_sector_lists_are_omitted(self, minimal_scheme):
        minimal_scheme["eligibility_sectors_included"] = []
        minimal_scheme["eligibility_sectors_excluded"] = []
        text = _format_eligibility_chunk(minimal_scheme)
        assert "Eligible sectors" not in text
        assert "Excluded sectors" not in text

    def test_missing_optional_field_uses_default(self, minimal_scheme):
        del minimal_scheme["administered_by"]
        text = _format_eligibility_chunk(minimal_scheme)
        assert "Administered by: N/A" in text


class TestDocumentsFormatting:

    def test_renders_each_document_as_bullet(self):
        text = _format_documents_chunk("Test Scheme", ["PAN Card", "Udyam Certificate"])
        assert "- PAN Card" in text
        assert "- Udyam Certificate" in text

    def test_header_names_the_scheme(self):
        text = _format_documents_chunk("Test Scheme", ["PAN Card"])
        assert text.startswith("Documents required to apply for Test Scheme:")


class TestLoadAllChunks:

    def test_loads_every_scheme_in_directory(self, tmp_path, minimal_scheme):
        for i in range(3):
            scheme = dict(minimal_scheme, scheme_id=f"scheme_{i}", name=f"Scheme {i}")
            (tmp_path / f"scheme_{i}.json").write_text(json.dumps(scheme))

        chunks = load_all_chunks(tmp_path)
        assert len(chunks) == 6
        assert len({c.scheme_id for c in chunks}) == 3

    def test_empty_directory_returns_empty_list(self, tmp_path):
        assert load_all_chunks(tmp_path) == []

    def test_mixed_enrichment_produces_correct_counts(self, tmp_path, minimal_scheme):
        enriched = dict(minimal_scheme, scheme_id="a", documents_required=["PAN Card"])
        plain = dict(minimal_scheme, scheme_id="b")
        (tmp_path / "a.json").write_text(json.dumps(enriched))
        (tmp_path / "b.json").write_text(json.dumps(plain))

        chunks = load_all_chunks(tmp_path)
        assert len(chunks) == 5
        assert sum(1 for c in chunks if c.chunk_type == "documents") == 1


class TestRealCorpus:
    """Guards against regressions in the actual scheme corpus."""

    def test_all_real_schemes_chunk_without_error(self):
        chunks = load_all_chunks(Path("data/schemes"))
        assert len(chunks) > 0

    def test_no_duplicate_chunk_ids_in_corpus(self):
        chunks = load_all_chunks(Path("data/schemes"))
        ids = [c.chunk_id for c in chunks]
        assert len(set(ids)) == len(ids)

    def test_no_empty_chunk_text_in_corpus(self):
        chunks = load_all_chunks(Path("data/schemes"))
        empty = [c.chunk_id for c in chunks if not c.text.strip()]
        assert empty == [], f"Empty chunks: {empty}"