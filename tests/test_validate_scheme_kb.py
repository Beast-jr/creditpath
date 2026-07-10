"""Tests for the scheme KB validator's per-file validation logic."""

import json

import jsonschema

from scripts.validate_scheme_kb import validate_file, load_schema


def _validator() -> jsonschema.Draft7Validator:
    return jsonschema.Draft7Validator(load_schema())


def _valid_scheme() -> dict:
    return {
        "scheme_id": "sample_scheme",
        "name": "Sample MSME Scheme",
        "administered_by": "Ministry of MSME",
        "scheme_type": "term_loan",
        "target_segments": ["micro"],
        "loan_range_min": 50000,
        "loan_range_max": 1000000,
        "interest_rate_min": 7.0,
        "interest_rate_max": 12.0,
        "collateral_required": False,
        "eligibility_vintage_months_min": 0,
        "eligibility_gst_required": False,
        "eligibility_sectors_included": [],
        "eligibility_sectors_excluded": [],
        "eligibility_geographic_restriction": "",
        "retrieval_text": "A sample scheme used only for validator testing purposes.",
        "official_url": "https://example.gov.in/",
        "last_verified_date": "2026-07-10"
    }


def _write(tmp_path, obj):
    p = tmp_path / "scheme.json"
    if isinstance(obj, str):
        p.write_text(obj)
    else:
        p.write_text(json.dumps(obj))
    return p


def test_valid_file_passes(tmp_path):
    p = _write(tmp_path, _valid_scheme())
    assert validate_file(p, _validator()) == []


def test_missing_field_reported(tmp_path):
    bad = _valid_scheme()
    del bad["name"]
    p = _write(tmp_path, bad)
    errors = validate_file(p, _validator())
    assert any("name" in e for e in errors)


def test_bad_enum_reported(tmp_path):
    bad = _valid_scheme()
    bad["scheme_type"] = "bogus"
    p = _write(tmp_path, bad)
    assert validate_file(p, _validator())  # non-empty = failure detected


def test_extra_field_reported(tmp_path):
    bad = _valid_scheme()
    bad["surprise_field"] = 123
    p = _write(tmp_path, bad)
    assert validate_file(p, _validator())


def test_malformed_json_reported(tmp_path):
    p = _write(tmp_path, "{ not valid json ]")
    errors = validate_file(p, _validator())
    assert any("invalid JSON" in e for e in errors)