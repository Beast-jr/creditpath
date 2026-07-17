import streamlit as st
from app.pages.assessment import render_assessment_form
from app.pages.results import render_results
from app.pages.schemes import render_schemes
from app.pages.whatif import render_whatif
import app.api_client as api_client

st.set_page_config(
    page_title="CreditPath",
    page_icon="💳",
    layout="wide",
    initial_sidebar_state="collapsed",
)

if "page" not in st.session_state:
    st.session_state.page = "assessment"

page = st.session_state.page

if page == "assessment":
    profile_data = render_assessment_form()
    if profile_data is not None:
        with st.spinner("Analysing your business profile..."):
            try:
                result = api_client.assess(profile_data)
                st.session_state.assessment_result = result
                st.session_state.profile_data = profile_data
                st.session_state.page = "results"
                st.rerun()
            except ConnectionError as e:
                st.error(str(e))
            except TimeoutError as e:
                st.error(str(e))
            except ValueError as e:
                st.error(str(e))
            except Exception as e:
                st.error(f"Something went wrong: {e}")

elif page == "results":
    if "assessment_result" not in st.session_state:
        st.session_state.page = "assessment"
        st.rerun()
    else:
        render_results(st.session_state.assessment_result)

elif page == "schemes":
    if "assessment_result" not in st.session_state:
        st.session_state.page = "assessment"
        st.rerun()
    else:
        render_schemes(st.session_state.assessment_result)

elif page == "whatif":
    render_whatif()

else:
    st.session_state.page = "assessment"
    st.rerun()
