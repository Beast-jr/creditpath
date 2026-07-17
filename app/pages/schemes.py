import streamlit as st
from app.components.scheme_card import render_scheme_card


def render_schemes(result: dict):
    st.title("Recommended Government Schemes")

    recommendations = result.get("recommendations", {})
    matches = recommendations.get("matches", [])
    total_found = recommendations.get("total_found", 0)

    if not matches:
        st.warning("No schemes matched your profile. Try improving your loan readiness score first.")
        if st.button("Back to Results"):
            st.session_state.page = "results"
            st.rerun()
        return

    st.markdown(
        f"We found **{total_found} eligible schemes** for your business. "
        f"Here are the top {len(matches)} ranked by how well they match your profile."
    )
    st.markdown("---")

    for i, match in enumerate(matches, 1):
        render_scheme_card(match, i)

    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Back to Results", use_container_width=True):
            st.session_state.page = "results"
            st.rerun()
    with col2:
        if st.button("Try What-If Scenarios", use_container_width=True):
            st.session_state.page = "whatif"
            st.rerun()
