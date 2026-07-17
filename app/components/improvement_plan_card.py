import streamlit as st


def render_improvement_plan(plan: dict):
    actions = plan.get("actions", [])
    if not actions:
        st.info("No improvement actions generated.")
        return

    st.markdown("### Your Improvement Roadmap")

    effort_colors = {"LOW": "#2ecc71", "MEDIUM": "#f39c12", "HIGH": "#e74c3c"}

    for i, action in enumerate(actions, 1):
        effort = action.get("effort_level", "MEDIUM")
        color = effort_colors.get(effort, "#95a5a6")
        delta = action.get("expected_score_delta", 0)
        weeks = action.get("timeline_weeks", 0)

        with st.expander(
            f"Action {i}: {action.get('description', '')} "
            f"(+{delta} pts, {weeks} weeks)",
            expanded=(i == 1),
        ):
            col1, col2, col3 = st.columns(3)
            col1.metric("Score Impact", f"+{delta} pts")
            col2.metric("Timeline", f"{weeks} weeks")
            col3.markdown(
                f'<span style="background:{color};color:white;padding:4px 10px;'
                f'border-radius:12px;font-size:0.8em">{effort} effort</span>',
                unsafe_allow_html=True,
            )

            st.markdown("**Steps to take:**")
            for step in action.get("specific_steps", []):
                st.markdown(f"- {step}")

    milestones = plan.get("milestones", [])
    if milestones:
        st.markdown("### Milestones")
        for m in milestones:
            st.markdown(f"**Week {m.get('target_week')}** — {m.get('title')}")
