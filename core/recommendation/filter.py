"""Hard eligibility filter for financing schemes.

Runs before any vector retrieval. Eliminates schemes the business
cannot legally qualify for based on structured fields alone.
"""

import json
import logging
from pathlib import Path
from typing import List

from core.schema import BusinessProfile, SchemeDocument

logger = logging.getLogger(__name__)

SCHEMES_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "schemes"


def _load_all_schemes() -> List[SchemeDocument]:
    """Load every scheme JSON from data/schemes/ into SchemeDocument objects."""
    schemes = []
    for path in sorted(SCHEMES_DIR.glob("*.json")):
        data = json.loads(path.read_text())
        schemes.append(SchemeDocument(**data))
    return schemes


class ConstraintFilter:
    """Eliminates ineligible schemes before retrieval.

    Each eligibility condition is a private method returning bool.
    filter() runs all six checks and returns only passing schemes.
    """

    def __init__(self, schemes: List[SchemeDocument] | None = None):
        """Load schemes from disk if not provided (allows injection for tests)."""
        self._schemes = schemes if schemes is not None else _load_all_schemes()

    def filter(self, profile: BusinessProfile) -> List[SchemeDocument]:
        """Return schemes the profile is eligible for.

        Runs all six checks per scheme. Logs every rejection with reason.
        """
        eligible = []
        for scheme in self._schemes:
            passed, reason = self._evaluate(profile, scheme)
            if passed:
                eligible.append(scheme)
            else:
                logger.debug(
                    "FILTERED %s for profile '%s': %s",
                    scheme.scheme_id,
                    profile.business_name,
                    reason,
                )
        logger.info(
            "Filter result for '%s': %d/%d schemes eligible",
            profile.business_name,
            len(eligible),
            len(self._schemes),
        )
        return eligible

    def _evaluate(self, profile: BusinessProfile, scheme: SchemeDocument):
        """Run all checks; return (True, '') or (False, reason)."""
        checks = [
            (self._check_vintage,      "vintage"),
            (self._check_loan_amount,  "loan_amount"),
            (self._check_collateral,   "collateral"),
            (self._check_sector,       "sector"),
            (self._check_geography,    "geography"),
            (self._check_gst_requirement, "gst"),
        ]
        for check_fn, label in checks:
            if not check_fn(profile, scheme):
                return False, label
        return True, ""

    # ── Individual eligibility checks ────────────────────────────

    def _check_vintage(self, profile: BusinessProfile, scheme: SchemeDocument) -> bool:
        """Business must meet minimum vintage requirement."""
        return profile.vintage_months >= scheme.eligibility_vintage_months_min

    def _check_loan_amount(self, profile: BusinessProfile, scheme: SchemeDocument) -> bool:
        """Loan sought must fit within scheme's range.

        If loan_range_min and loan_range_max are both 0, the scheme is a
        pure subsidy/support scheme with no loan component — always passes.
        """
        if scheme.loan_range_min == 0 and scheme.loan_range_max == 0:
            return True
        return scheme.loan_range_min <= profile.loan_amount_sought_inr <= scheme.loan_range_max

    def _check_collateral(self, profile: BusinessProfile, scheme: SchemeDocument) -> bool:
        """If scheme requires collateral, profile must have it."""
        if not scheme.collateral_required:
            return True
        return profile.has_collateral

    def _check_sector(self, profile: BusinessProfile, scheme: SchemeDocument) -> bool:
        """Sector must not be excluded; if included list non-empty, must be in it."""
        sector = profile.sector.lower().strip()
        excluded = [s.lower().strip() for s in scheme.eligibility_sectors_excluded]
        if sector in excluded:
            return False
        included = [s.lower().strip() for s in scheme.eligibility_sectors_included]
        if included and sector not in included:
            return False
        return True

    def _check_geography(self, profile: BusinessProfile, scheme: SchemeDocument) -> bool:
        """If scheme has a geographic restriction, profile's state must match."""
        restriction = scheme.eligibility_geographic_restriction.strip()
        if not restriction:
            return True
        return profile.state.lower().strip() == restriction.lower().strip()

    def _check_gst_requirement(self, profile: BusinessProfile, scheme: SchemeDocument) -> bool:
        """If scheme requires GST registration, profile must have filed GST."""
        if not scheme.eligibility_gst_required:
            return True
        return profile.gst_filing_rate_pct > 0