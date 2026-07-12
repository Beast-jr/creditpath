"""Train K-Means cluster model on golden personas.

One-time script. Safe to re-run — overwrites existing model.

Usage:
    python -m scripts.train_clusters
"""

import json
import logging
import sys
from pathlib import Path

from core.clustering.model import ProfileClusterer
from core.schema import BusinessProfile

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)

GOLDEN_PATH = Path("tests/fixtures/golden_personas.json")


def main() -> int:
    personas = json.loads(GOLDEN_PATH.read_text())
    profiles = [
        BusinessProfile(**{k: v for k, v in p.items() if k != "expected_tier"})
        for p in personas
    ]
    logger.info("Training cluster model on %d profiles…", len(profiles))
    clusterer = ProfileClusterer()
    clusterer.train(profiles)
    logger.info("Done.")
    return 0


if __name__ == "__main__":
    sys.exit(main())