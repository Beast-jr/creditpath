import streamlit as st
import app.api_client as api_client


def render_chat(result: dict):
    scorecard = result.get("scorecard", {})
    weighted_score = scorecard.get("weighted_score")
    tier = scorecard.get("tier")
    profile_data = st.session_state.get("profile_data", {})

    st.markdown("## Ask about your schemes")
    st.caption(
        "Ask about eligibility, loan amounts, collateral, or required documents "
        "for the financing schemes. Answers are grounded in official scheme data."
    )

    # Back navigation, consistent with other pages
    if st.button("← Back to results"):
        st.session_state.page = "results"
        st.rerun()

    # Initialise chat history for this feature
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    # Suggested starter questions
    if not st.session_state.chat_history:
        st.markdown("**Try asking:**")
        suggestions = [
            "What documents do I need for CGTMSE?",
            "Which schemes don't require collateral?",
            "Am I eligible for MUDRA Tarun?",
        ]
        cols = st.columns(len(suggestions))
        for col, q in zip(cols, suggestions):
            if col.button(q, key=f"suggest_{q}"):
                st.session_state.pending_question = q
                st.rerun()

    # Render existing history
    for turn in st.session_state.chat_history:
        with st.chat_message("user"):
            st.markdown(turn["question"])
        with st.chat_message("assistant"):
            st.markdown(turn["answer"])
            if turn["sources"]:
                with st.expander("Sources"):
                    for s in turn["sources"]:
                        name = s["scheme_name"]
                        url = s["official_url"]
                        if url:
                            st.markdown(f"- [{name}]({url})")
                        else:
                            st.markdown(f"- {name}")

    # Input: either a clicked suggestion or typed question
    question = st.chat_input("Ask a question about your schemes...")
    if "pending_question" in st.session_state:
        question = st.session_state.pop("pending_question")

    if question:
        with st.chat_message("user"):
            st.markdown(question)

        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    response = api_client.chat(
                        question=question,
                        profile_dict=profile_data,
                        weighted_score=weighted_score,
                        tier=tier,
                    )
                    answer = response["answer"]
                    sources = response["sources"]
                    st.markdown(answer)
                    if sources:
                        with st.expander("Sources"):
                            for s in sources:
                                name = s["scheme_name"]
                                url = s["official_url"]
                                if url:
                                    st.markdown(f"- [{name}]({url})")
                                else:
                                    st.markdown(f"- {name}")
                    st.session_state.chat_history.append({
                        "question": question,
                        "answer": answer,
                        "sources": sources,
                    })
                except (ConnectionError, TimeoutError, ValueError) as e:
                    st.error(str(e))
                except Exception as e:
                    st.error(f"Something went wrong: {e}")
