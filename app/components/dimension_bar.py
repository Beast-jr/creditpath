import streamlit as st


def render_dimension_bar(dimension_name: str, score: float, label: str, reason: str):
    label_colors = {
        "STRONG": "#2ecc71",
        "ADEQUATE": "#f39c12",
        "WEAK": "#e67e22",
        "CRITICAL": "#e74c3c",
    }
    color = label_colors.get(label, "#95a5a6")
    label_display = {
        "STRONG": "Strong",
        "ADEQUATE": "Adequate",
        "WEAK": "Weak",
        "CRITICAL": "Critical",
    }.get(label, label)

    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown(f"**{dimension_name}**")
        st.progress(int(score))
        st.caption(reason)
    with col2:
        st.markdown(
            f'<span style="background:{color};color:white;padding:4px 10px;'
            f'border-radius:12px;font-size:0.8em;font-weight:bold">'
            f'{label_display}</span>',
            unsafe_allow_html=True,
        )
    st.markdown("---")
