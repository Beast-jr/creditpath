import streamlit as st


def render_scheme_card(match: dict, rank: int):
    scheme_id = match.get("scheme_id", "")
    name = match.get("scheme_name", "Unknown Scheme")
    score = match.get("match_score", 0)
    explanation = match.get("eligibility_explanation", "")
    loan_min = match.get("loan_range_min", 0)
    loan_max = match.get("loan_range_max", 0)
    rate_min = match.get("interest_rate_min", 0)
    rate_max = match.get("interest_rate_max", 0)
    url = match.get("official_url", "")

    # Loan range display
    if loan_min == 0 and loan_max == 0:
        loan_str = "Subsidy / Grant (no loan component)"
    elif loan_max == 0:
        loan_str = f"Rs {loan_min:,}+"
    else:
        loan_str = f"Rs {loan_min:,} – Rs {loan_max:,}"

    # Interest rate display
    if rate_min == 0 and rate_max == 0:
        rate_str = "Set by lender"
    elif rate_min == rate_max:
        rate_str = f"{rate_min}%"
    else:
        rate_str = f"{rate_min}% – {rate_max}%"

    # Match score bar color
    if score >= 0.7:
        bar_color = "#2ecc71"
    elif score >= 0.5:
        bar_color = "#f39c12"
    else:
        bar_color = "#e67e22"

    with st.container():
        st.markdown(
            f'<div style="border:1px solid #e0e0e0;border-radius:12px;padding:16px;margin-bottom:12px">'
            f'<div style="display:flex;justify-content:space-between;align-items:center">'
            f'<h4 style="margin:0">#{rank} {name}</h4>'
            f'<span style="background:{bar_color};color:white;padding:4px 10px;'
            f'border-radius:12px;font-size:0.85em">Match: {score:.0%}</span>'
            f'</div>'
            f'<div style="margin-top:8px;display:flex;gap:24px">'
            f'<span>💰 <b>Loan:</b> {loan_str}</span>'
            f'<span>📊 <b>Interest:</b> {rate_str}</span>'
            f'</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

        with st.expander("Why this scheme? + How to apply"):
            st.markdown(f"**Why you qualify:** {explanation}")
            if url:
                st.markdown(f"[Apply Now →]({url})", unsafe_allow_html=False)
                st.caption(f"Official link: {url}")

        st.markdown("")
