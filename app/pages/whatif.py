import streamlit as st
import app.api_client as api_client

DIMENSION_LABELS = {
    "gst_filing_rate_pct": "GST Filing Rate (%)",
    "revenue_consistency_pct": "Revenue Consistency (%)",
    "monthly_revenue_inr": "Monthly Revenue (Rs)",
    "existing_emi_inr": "Existing Monthly EMI (Rs)",
    "collateral_value_inr": "Collateral Value (Rs)",
    "vintage_months": "Business Age (months)",
}

TIER_ORDER = ["NOT_READY", "NEEDS_WORK", "NEARLY_READY", "LOAN_READY"]
TIER_LABELS = {
    "NOT_READY": "Not Ready",
    "NEEDS_WORK": "Needs Work",
    "NEARLY_READY": "Nearly Ready",
    "LOAN_READY": "Loan Ready",
}
TIER_COLORS = {
    "NOT_READY": "#e74c3c",
    "NEEDS_WORK": "#e67e22",
    "NEARLY_READY": "#f39c12",
    "LOAN_READY": "#2ecc71",
}


def render_whatif():
    st.title("What-If Scenarios")
    st.markdown("Adjust your business metrics to see how your loan readiness score changes — instantly, no waiting.")

    if "profile_data" not in st.session_state or "assessment_result" not in st.session_state:
        st.warning("Please complete an assessment first.")
        if st.button("Go to Assessment"):
            st.session_state.page = "assessment"
            st.rerun()
        return

    profile = dict(st.session_state.profile_data)
    original_result = st.session_state.assessment_result
    original_scorecard = original_result.get("scorecard", {})
    original_tier = original_scorecard.get("tier", "NOT_READY")
    original_score = original_scorecard.get("weighted_score", 0)
    original_schemes = len(original_result.get("recommendations", {}).get("matches", []))

    st.markdown(f"**Current score:** {original_score}/100 — {TIER_LABELS.get(original_tier, original_tier)}")
    st.markdown("---")

    st.subheader("Adjust Your Metrics")

    col1, col2, col3 = st.columns(3)

    with col1:
        new_gst = st.slider(
            "GST Filing Rate (%)",
            0, 100,
            int(profile.get("gst_filing_rate_pct", 80)),
            help="Percentage of months you filed GST on time in the last 12 months",
        )

    with col2:
        new_consistency = st.slider(
            "Revenue Consistency (%)",
            0, 100,
            int(profile.get("revenue_consistency_pct", 75)),
            help="How consistent is your monthly revenue?",
        )

    with col3:
        new_emi = st.number_input(
            "Monthly EMI (Rs)",
            min_value=0,
            value=int(profile.get("existing_emi_inr", 0)),
            step=500,
            help="Total of all existing loan EMIs per month",
        )

    if st.button("Recalculate", type="primary", use_container_width=True):
        modified_profile = {**profile}
        modified_profile["gst_filing_rate_pct"] = float(new_gst)
        modified_profile["revenue_consistency_pct"] = float(new_consistency)
        modified_profile["existing_emi_inr"] = float(new_emi)

        try:
            with st.spinner("Recalculating..."):
                result = api_client.whatif(modified_profile)

            new_scorecard = result.get("scorecard", {})
            new_tier = new_scorecard.get("tier", "NOT_READY")
            new_score = new_scorecard.get("weighted_score", 0)
            new_schemes = len(result.get("recommendations", {}).get("matches", []))

            score_delta = round(new_score - original_score, 2)
            scheme_delta = new_schemes - original_schemes

            st.markdown("---")
            st.subheader("Recalculation Results")

            col1, col2, col3 = st.columns(3)
            col1.metric("New Score", f"{new_score}/100", delta=f"{score_delta:+.2f}")
            col2.metric("Tier", TIER_LABELS.get(new_tier, new_tier),
                delta="improved" if TIER_ORDER.index(new_tier) > TIER_ORDER.index(original_tier) else None)
            col3.metric("Matching Schemes", new_schemes, delta=scheme_delta if scheme_delta != 0 else None)

            if new_tier != original_tier:
                color = TIER_COLORS.get(new_tier, "#95a5a6")
                if TIER_ORDER.index(new_tier) > TIER_ORDER.index(original_tier):
                    st.success(
                        f"With these changes, your tier improves from "
                        f"**{TIER_LABELS[original_tier]}** to **{TIER_LABELS[new_tier]}**!"
                    )
                else:
                    st.warning(
                        f"These changes would move your tier from "
                        f"**{TIER_LABELS[original_tier]}** to **{TIER_LABELS[new_tier]}**."
                    )
            else:
                if score_delta > 0:
                    st.info(f"Your score improves by {score_delta} points but stays in the same tier.")
                elif score_delta < 0:
                    st.warning(f"Your score decreases by {abs(score_delta)} points.")
                else:
                    st.info("No change in score with these adjustments.")

        except ConnectionError as e:
            st.error(str(e))
        except TimeoutError as e:
            st.error(str(e))
        except Exception as e:
            st.error(f"Recalculation failed: {e}")

    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Back to Results", use_container_width=True):
            st.session_state.page = "results"
            st.rerun()
    with col2:
        if st.button("View Schemes", use_container_width=True):
            st.session_state.page = "schemes"
            st.rerun()
