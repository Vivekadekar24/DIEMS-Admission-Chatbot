
import re
import streamlit as st

from backend.services.retriever import retriever
from backend.services.llm_service import llm_service

st.set_page_config(
    page_title="DIEMS Admission Assistant",
    page_icon="🎓",
    layout="centered",
)

st.title("🎓 DIEMS Admission Enquiry Chatbot")
st.caption(
    "Deogiri Institute of Engineering and Management Studies"
)

if not retriever.ready:
    st.error(
        "The knowledge index could not be loaded. "
        "Rebuild it with: venv\\Scripts\\python -m backend.services.ingest"
    )
    st.code(retriever.error or "Knowledge index unavailable")
    st.stop()


def retrieval_answer(question, results):
    """Use the configured LLM when available, otherwise return verified text."""
    context = "\n\n".join(result["text"] for result in results)
    answer = re.split(r"\nanswer:\s*", results[0]["text"], maxsplit=1, flags=re.IGNORECASE)[-1]
    answer = re.split(r"\n(?:category|source):\s*", answer, maxsplit=1, flags=re.IGNORECASE)[0].strip()
    return llm_service.answer(question, context) or answer

if "messages" not in st.session_state:
    st.session_state.messages = []

with st.sidebar:
    st.header("Quick Questions")
    questions = [
        "Which B.Tech branches are offered?",
        "What are the B.Tech fees for 2026-27?",
        "Which documents are required?",
        "Does DIEMS provide hostel facilities?",
    ]

    for question in questions:
        if st.button(question, use_container_width=True):
            st.session_state.pending_question = question

    if st.button("New conversation", use_container_width=True):
        st.session_state.messages = []
        st.session_state.pop("pending_question", None)
        st.rerun()

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

        if message.get("sources"):
            st.caption("Sources: " + ", ".join(message["sources"]))

question = st.chat_input("Ask about courses, fees or admissions...")

if not question:
    question = st.session_state.pop("pending_question", None)

if question:
    st.session_state.messages.append(
        {"role": "user", "content": question}
    )

    with st.chat_message("user"):
        st.markdown(question)

    with st.chat_message("assistant"):
        with st.spinner("Finding DIEMS information..."):
            try:
                results = retriever.search(question)

                if not results or results[0]["score"] < 0.30:
                    answer = (
                        "I couldn't find a reliable answer in the "
                        "available DIEMS documents. Please contact "
                        "the college admission office for confirmation."
                    )
                    sources = []
                else:
                    answer = retrieval_answer(question, results)
                    sources = list(dict.fromkeys(
                        result.get("metadata", {}).get(
                            "source", "DIEMS knowledge base"
                        )
                        for result in results
                    ))[:4]

                st.markdown(answer)

                if sources:
                    st.caption("Sources: " + ", ".join(sources))

                st.session_state.messages.append({
                    "role": "assistant",
                    "content": answer,
                    "sources": sources,
                })

            except Exception:
                st.error(
                    "An error occurred while processing your question. "
                    "Please check the application logs."
                )
