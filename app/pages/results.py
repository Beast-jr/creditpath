import streamlit as st
from app.components.dimension_bar import render_dimension_bar
from app.components.improvement_plan_card import render_improvement_plan

TIER_CONFIG = {
    "LOAN_READY":   {"label": "Loan Ready",    "color": "#2ecc71", "emoji": "✅"},
    "NEARLY_READY": {"label": "Nearly Ready",  "color": "#f39c12", "emoji": "🟡"},
    "NEEDS_WORK":   {"label": "Needs Work",    "color": "#e67e22", "emoji": "🟠"},
    "NOT_READY":    {"label": "Not Ready",     "color": "#e74c3c", "emoji": "❌"},
}


def render_results(result: dict):
    scorecard = result.get("scorecard", {})
    tier = scorecard.get("tier", "NOT_READY")
    score = scorecard.get("weighted_score", 0)
    config = TIER_CONFIG.get(tier, TIER_CONFIG["NOT_READY"])

    # Tier badge
    st.markdown(
        f'<div style="background:{config["color"]};color:white;padding:16px;'
        f'border-radius:12px;text-align:center;margin-bottom:20px">'
        f'<h2 style="margin:0">{config["emoji"]} {config["label"]}</h2>'
        f'<p style="margin:4px 0 0 0;font-size:1.2em">Score: {score}/100</p>'
        f'</div>',
        unsafe_allow_html=True,
    )

    # Cluster
    cluster = result.get("cluster", {})
    if cluster:
        st.info(f"**Your business profile:** {cluster.get('label', '')} — {cluster.get('peer_description', '')}")

    # Explanation
    explanation = result.get("explanation", "")
    if explanation:
        st.markdown("### What This Means")
        st.markdown(explanation)

    # Dimension scores
    st.markdown("### Scorecard Breakdown")
    for dim in scorecard.get("dimension_scores", []):
        render_dimension_bar(
            dimension_name=dim["dimension_name"],
            score=dim["score"],
            label=dim["label"],
            reason=dim["reason"],
        )

    # Improvement plan
    plan = result.get("improvement_plan", {})
    if plan and plan.get("actions"):
        render_improvement_plan(plan)

    # Navigation buttons
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("View Recommended Schemes", use_container_width=True):
            st.session_state.page = "schemes"
            st.rerun()
    with col2:
        if st.button("Try What-If Scenarios", use_container_width=True):
            st.session_state.page = "whatif"
            st.rerun()
    with col3:
        if st.button("Start New Assessment", use_container_width=True):
            for key in ["assessment_result", "profile_data", "page"]:
                st.session_state.pop(key, None)
            st.rerun()
