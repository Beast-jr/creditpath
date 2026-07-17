import streamlit as st

SECTORS = [
    "Automotive", "Construction", "Food & Beverage", "Grocery", "Healthcare",
    "Hospitality", "Logistics", "Manufacturing", "Pharmacy", "Retail",
    "Services", "Technology", "Textile", "Trading", "Other"
]

STATES = [
    "Andhra Pradesh", "Assam", "Bihar", "Delhi", "Gujarat", "Haryana",
    "Karnataka", "Kerala", "Madhya Pradesh", "Maharashtra", "Odisha",
    "Punjab", "Rajasthan", "Tamil Nadu", "Telangana", "Uttar Pradesh",
    "Uttarakhand", "West Bengal", "Other"
]


def render_assessment_form():
    st.title("CreditPath — Loan Readiness Assessment")
    st.markdown("Fill in your business details to check your loan readiness and discover government schemes.")

    with st.form("assessment_form"):
        st.subheader("Business Information")
        col1, col2 = st.columns(2)
        with col1:
            business_name = st.text_input("Business Name", placeholder="e.g. Kumar Auto Spares")
            sector = st.selectbox("Sector", SECTORS)
            city = st.text_input("City", placeholder="e.g. Hubli")
        with col2:
            owner_name = st.text_input("Owner Name", placeholder="e.g. Ramesh Kumar")
            state = st.selectbox("State", STATES)
            geographic_tier = st.selectbox("City Type", [1, 2, 3],
                format_func=lambda x: {1: "Metro (Tier 1)", 2: "Mid-size (Tier 2)", 3: "Small town (Tier 3)"}[x])

        st.subheader("Financial Details")
        col1, col2 = st.columns(2)
        with col1:
            monthly_revenue_inr = st.number_input("Monthly Revenue (Rs)", min_value=1000, value=100000, step=1000)
            existing_emi_inr = st.number_input("Existing Monthly EMI (Rs)", min_value=0, value=0, step=500)
            gst_filing_rate_pct = st.slider("GST Filing Rate (%)", 0, 100, 80,
                help="Percentage of months you filed GST returns on time in the last 12 months")
        with col2:
            revenue_consistency_pct = st.slider("Revenue Consistency (%)", 0, 100, 75,
                help="How consistent is your monthly revenue? 100% means same revenue every month")
            vintage_months = st.number_input("Business Age (months)", min_value=0, value=24, step=1)
            loan_amount_sought_inr = st.number_input("Loan Amount Needed (Rs)", min_value=10000, value=500000, step=10000)

        st.subheader("Collateral")
        has_collateral = st.checkbox("I have assets to offer as collateral (property, equipment, gold, etc.)")
        collateral_value_inr = 0
        if has_collateral:
            collateral_value_inr = st.number_input("Estimated Collateral Value (Rs)", min_value=0, value=500000, step=10000)

        submitted = st.form_submit_button("Check My Loan Readiness", type="primary", use_container_width=True)

    if submitted:
        if not business_name.strip():
            st.error("Please enter your business name.")
            return
        if not owner_name.strip():
            st.error("Please enter the owner name.")
            return
        if not city.strip():
            st.error("Please enter your city.")
            return

        return {
            "business_name": business_name.strip(),
            "owner_name": owner_name.strip(),
            "sector": sector,
            "city": city.strip(),
            "state": state,
            "geographic_tier": geographic_tier,
            "monthly_revenue_inr": float(monthly_revenue_inr),
            "revenue_consistency_pct": float(revenue_consistency_pct),
            "existing_emi_inr": float(existing_emi_inr),
            "gst_filing_rate_pct": float(gst_filing_rate_pct),
            "vintage_months": int(vintage_months),
            "has_collateral": has_collateral,
            "collateral_value_inr": float(collateral_value_inr),
            "loan_amount_sought_inr": float(loan_amount_sought_inr),
        }
    return None
