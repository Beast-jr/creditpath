"""Tests for core/clustering/model.py"""

import json
from pathlib import Path

import pytest

from core.clustering.model import (
    CLUSTER_DESCRIPTIONS,
    CLUSTER_LABELS,
    N_CLUSTERS,
    ProfileClusterer,
)
from core.schema import BusinessProfile, ClusterAssignment

GOLDEN_PATH = Path("tests/fixtures/golden_personas.json")
GOLDEN_PERSONAS = json.loads(GOLDEN_PATH.read_text())


def _make_profile(**overrides) -> BusinessProfile:
    defaults = dict(
        business_name="Test Co",
        owner_name="Test Owner",
        sector="manufacturing",
        city="Bengaluru",
        state="karnataka",
        geographic_tier=2,
        monthly_revenue_inr=500_000,
        revenue_consistency_pct=80.0,
        existing_emi_inr=10_000,
        gst_filing_rate_pct=90.0,
        vintage_months=36,
        has_collateral=True,
        collateral_value_inr=1_000_000,
        loan_amount_sought_inr=500_000,
    )
    defaults.update(overrides)
    return BusinessProfile(**defaults)


def _make_profiles_from_golden() -> list:
    return [
        BusinessProfile(**{k: v for k, v in p.items() if k != "expected_tier"})
        for p in GOLDEN_PERSONAS
    ]


# ── Label and description completeness ──────────────────────────

def test_all_cluster_ids_have_labels():
    for i in range(N_CLUSTERS):
        assert i in CLUSTER_LABELS
        assert len(CLUSTER_LABELS[i]) > 0


def test_all_cluster_ids_have_descriptions():
    for i in range(N_CLUSTERS):
        assert i in CLUSTER_DESCRIPTIONS
        assert len(CLUSTER_DESCRIPTIONS[i]) > 10


# ── Featurize ───────────────────────────────────────────────────

def test_featurize_returns_correct_shape():
    clusterer = ProfileClusterer()
    profile = _make_profile()
    features = clusterer._featurize(profile)
    assert features.shape == (9,)


def test_featurize_has_no_nan():
    import numpy as np
    clusterer = ProfileClusterer()
    profile = _make_profile()
    features = clusterer._featurize(profile)
    assert not np.any(np.isnan(features))


def test_featurize_collateral_bool_converted():
    clusterer = ProfileClusterer()
    p_with = _make_profile(has_collateral=True)
    p_without = _make_profile(has_collateral=False)
    f_with = clusterer._featurize(p_with)
    f_without = clusterer._featurize(p_without)
    assert f_with[5] == 1.0
    assert f_without[5] == 0.0


# ── Train ────────────────────────────────────────────────────────

def test_train_saves_model_file(tmp_path, monkeypatch):
    import core.clustering.model as m
    monkeypatch.setattr(m, "MODEL_PATH", tmp_path / "cluster_model.pkl")
    clusterer = ProfileClusterer()
    profiles = _make_profiles_from_golden()
    clusterer.train(profiles)
    assert (tmp_path / "cluster_model.pkl").exists()


def test_train_requires_minimum_profiles():
    clusterer = ProfileClusterer()
    with pytest.raises(ValueError, match="at least"):
        clusterer.train([_make_profile()])


# ── Assign ───────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def trained_clusterer(tmp_path_factory):
    import core.clustering.model as m
    tmp = tmp_path_factory.mktemp("model")
    original_path = m.MODEL_PATH
    m.MODEL_PATH = tmp / "cluster_model.pkl"
    clusterer = ProfileClusterer()
    clusterer.train(_make_profiles_from_golden())
    yield clusterer
    m.MODEL_PATH = original_path


def test_assign_returns_cluster_assignment(trained_clusterer):
    result = trained_clusterer.assign(_make_profile())
    assert isinstance(result, ClusterAssignment)


def test_assign_cluster_id_in_range(trained_clusterer):
    result = trained_clusterer.assign(_make_profile())
    assert 0 <= result.cluster_id < N_CLUSTERS


def test_assign_label_is_nonempty_string(trained_clusterer):
    result = trained_clusterer.assign(_make_profile())
    assert isinstance(result.label, str)
    assert len(result.label) > 0


def test_assign_peer_description_is_nonempty(trained_clusterer):
    result = trained_clusterer.assign(_make_profile())
    assert isinstance(result.peer_description, str)
    assert len(result.peer_description) > 10


def test_assign_centroid_distance_nonnegative(trained_clusterer):
    result = trained_clusterer.assign(_make_profile())
    assert result.centroid_distance >= 0.0


def test_all_golden_personas_get_assigned(trained_clusterer):
    profiles = _make_profiles_from_golden()
    for profile in profiles:
        result = trained_clusterer.assign(profile)
        assert 0 <= result.cluster_id < N_CLUSTERS


def test_similar_profiles_same_cluster(trained_clusterer):
    """Two very similar profiles should land in the same cluster."""
    p1 = _make_profile(monthly_revenue_inr=500_000, vintage_months=36)
    p2 = _make_profile(monthly_revenue_inr=520_000, vintage_months=38)
    r1 = trained_clusterer.assign(p1)
    r2 = trained_clusterer.assign(p2)
    assert r1.cluster_id == r2.cluster_id


def test_very_different_profiles_may_differ(trained_clusterer):
    """A micro startup and a large mature enterprise should differ."""
    startup = _make_profile(
        monthly_revenue_inr=60_000,
        vintage_months=8,
        has_collateral=False,
        collateral_value_inr=0,
        loan_amount_sought_inr=100_000,
    )
    mature = _make_profile(
        monthly_revenue_inr=1_500_000,
        vintage_months=96,
        has_collateral=True,
        collateral_value_inr=5_000_000,
        loan_amount_sought_inr=2_000_000,
    )
    r1 = trained_clusterer.assign(startup)
    r2 = trained_clusterer.assign(mature)
    # They should be in different clusters — if not, K=4 may need revisiting
    assert r1.cluster_id != r2.cluster_id