"""Validates data/scheme_schema.json loads and a sample scheme conforms."""

import json
import re
from pathlib import Path

import jsonschema
import pytest

SCHEMA_PATH = Path("data/scheme_schema.json")
SCHEMES_DIR = Path("data/schemes")


def _schema() -> dict:
    with open(SCHEMA_PATH) as f:
        return json.load(f)


def _valid_scheme() -> dict:
    return {
        "scheme_id": "cgtmse_credit_guarantee",
        "name": "Credit Guarantee Fund Trust for Micro and Small Enterprises",
        "administered_by": "SIDBI and Ministry of MSME",
        "scheme_type": "credit_guarantee",
        "target_segments": ["micro", "small", "no_collateral"],
        "loan_range_min": 100000,
        "loan_range_max": 20000000,
        "interest_rate_min": 8.0,
        "interest_rate_max": 14.0,
        "collateral_required": False,
        "eligibility_vintage_months_min": 0,
        "eligibility_gst_required": False,
        "eligibility_sectors_included": [],
        "eligibility_sectors_excluded": ["retail_trade"],
        "eligibility_geographic_restriction": "",
        "retrieval_text": "Collateral-free credit guarantee for micro and small enterprises up to Rs 2 crore.",
        "official_url": "https://www.cgtmse.in/",
        "last_verified_date": "2026-07-10",
    }


def test_schema_is_valid_jsonschema():
    jsonschema.Draft7Validator.check_schema(_schema())


def test_valid_scheme_passes():
    jsonschema.validate(_valid_scheme(), _schema())


def test_missing_required_field_fails():
    bad = _valid_scheme()
    del bad["scheme_id"]
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(bad, _schema())


def test_bad_scheme_type_fails():
    bad = _valid_scheme()
    bad["scheme_type"] = "not_a_real_type"
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(bad, _schema())


def test_bad_url_fails():
    bad = _valid_scheme()
    bad["official_url"] = "ftp://nope"
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(bad, _schema())


# ── Day 13: Cross-validation tests ──────────────────────────────


def _load_all_schemes():
    """Load every scheme JSON file as (scheme_id, dict) pairs."""
    results = []
    for path in sorted(SCHEMES_DIR.glob("*.json")):
        data = json.loads(path.read_text())
        results.append((data.get("scheme_id", path.stem), data))
    return results


ALL_SCHEMES = _load_all_schemes()


@pytest.mark.parametrize("scheme_id,data", ALL_SCHEMES, ids=[s[0] for s in ALL_SCHEMES])
def test_loan_range_max_gte_min(scheme_id, data):
    assert data["loan_range_max"] >= data["loan_range_min"], (
        f"{scheme_id}: loan_range_max {data['loan_range_max']} < min {data['loan_range_min']}"
    )


@pytest.mark.parametrize("scheme_id,data", ALL_SCHEMES, ids=[s[0] for s in ALL_SCHEMES])
def test_interest_rate_max_gte_min(scheme_id, data):
    assert data["interest_rate_max"] >= data["interest_rate_min"], (
        f"{scheme_id}: interest_rate_max {data['interest_rate_max']} < min {data['interest_rate_min']}"
    )


@pytest.mark.parametrize("scheme_id,data", ALL_SCHEMES, ids=[s[0] for s in ALL_SCHEMES])
def test_retrieval_text_min_length(scheme_id, data):
    text = data.get("retrieval_text", "")
    assert len(text) >= 50, (
        f"{scheme_id}: retrieval_text only {len(text)} chars (need >= 50)"
    )


@pytest.mark.parametrize("scheme_id,data", ALL_SCHEMES, ids=[s[0] for s in ALL_SCHEMES])
def test_last_verified_date_format(scheme_id, data):
    date_str = data.get("last_verified_date", "")
    assert re.fullmatch(r"\d{4}-\d{2}-\d{2}", date_str), (
        f"{scheme_id}: last_verified_date '{date_str}' is not YYYY-MM-DD"
    )