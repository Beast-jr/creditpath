"""K-Means clustering for MSME business profiles.

Groups profiles into peer clusters for contextual comparison.
Model persisted at data/cluster_model.pkl — train once, load at runtime.
"""

import logging
import pickle
from pathlib import Path
from typing import List

import numpy as np
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

from core.schema import BusinessProfile, ClusterAssignment

logger = logging.getLogger(__name__)

MODEL_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "cluster_model.pkl"
N_CLUSTERS = 4  # chosen via elbow method (see notebooks/04_clustering_analysis.ipynb)

# Human-readable labels assigned after inspecting cluster centroids
CLUSTER_LABELS = {
    0: "Early-Stage Micro Enterprises",
    1: "Growth-Stage Small Businesses",
    2: "Established Asset-Backed MSMEs",
    3: "High-Revenue Mature Enterprises",
}

CLUSTER_DESCRIPTIONS = {
    0: "Early-stage micro businesses with limited vintage, lower revenue, and minimal collateral — typically seeking their first formal credit.",
    1: "Growing small businesses with moderate revenue consistency and some track record, actively expanding operations.",
    2: "Established MSMEs with collateral assets, strong GST compliance, and stable cash flows — well-positioned for term loans.",
    3: "Mature high-revenue enterprises with significant vintage and strong financial metrics, seeking larger credit facilities.",
}


class ProfileClusterer:
    """K-Means clusterer for business profiles.

    Train once with scripts/train_clusters.py.
    At runtime, call assign() to get a ClusterAssignment for a profile.
    """

    def __init__(self):
        self._scaler: StandardScaler | None = None
        self._kmeans: KMeans | None = None

    def _featurize(self, profile: BusinessProfile) -> np.ndarray:
        """Convert a BusinessProfile to a fixed-length numeric feature vector.

        Only creditworthiness-relevant numeric fields are included.
        Categorical fields (sector, city, state) are excluded.
        """
        return np.array([
            profile.monthly_revenue_inr,
            profile.revenue_consistency_pct,
            profile.existing_emi_inr,
            profile.gst_filing_rate_pct,
            profile.vintage_months,
            float(profile.has_collateral),       # bool → 0.0 / 1.0
            profile.collateral_value_inr,
            profile.loan_amount_sought_inr,
            float(profile.geographic_tier),
        ], dtype=float)

    def train(self, profiles: List[BusinessProfile]) -> None:
        """Fit scaler + K-Means on a list of profiles and save to disk.

        Args:
            profiles: Training profiles. In production, use golden personas
                      plus any collected assessment data.
        """
        if len(profiles) < N_CLUSTERS:
            raise ValueError(
                f"Need at least {N_CLUSTERS} profiles to train {N_CLUSTERS} clusters, "
                f"got {len(profiles)}"
            )

        X = np.array([self._featurize(p) for p in profiles])

        self._scaler = StandardScaler()
        X_scaled = self._scaler.fit_transform(X)

        self._kmeans = KMeans(
            n_clusters=N_CLUSTERS,
            random_state=42,
            n_init=10,
        )
        self._kmeans.fit(X_scaled)

        MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(MODEL_PATH, "wb") as f:
            pickle.dump({"scaler": self._scaler, "kmeans": self._kmeans}, f)

        logger.info(
            "Cluster model trained on %d profiles, K=%d, saved to %s",
            len(profiles), N_CLUSTERS, MODEL_PATH,
        )

    def _load(self) -> None:
        """Load scaler and K-Means from disk."""
        if not MODEL_PATH.exists():
            raise FileNotFoundError(
                f"Cluster model not found at {MODEL_PATH}. "
                "Run: python -m scripts.train_clusters"
            )
        with open(MODEL_PATH, "rb") as f:
            saved = pickle.load(f)
        self._scaler = saved["scaler"]
        self._kmeans = saved["kmeans"]

    def assign(self, profile: BusinessProfile) -> ClusterAssignment:
        """Assign a profile to its nearest cluster.

        Args:
            profile: The business profile to assign.

        Returns:
            ClusterAssignment with cluster_id, label, distance, and description.
        """
        if self._scaler is None or self._kmeans is None:
            self._load()

        x = self._featurize(profile).reshape(1, -1)
        x_scaled = self._scaler.transform(x)

        cluster_id = int(self._kmeans.predict(x_scaled)[0])
        centroid = self._kmeans.cluster_centers_[cluster_id]
        distance = float(np.linalg.norm(x_scaled[0] - centroid))

        return ClusterAssignment(
            cluster_id=cluster_id,
            label=CLUSTER_LABELS[cluster_id],
            centroid_distance=round(distance, 4),
            peer_description=CLUSTER_DESCRIPTIONS[cluster_id],
        )