
import streamlit as st

from backend.services.retriever import DiemsRetriever
from backend.services.llm_service import generate_answer

st.set_page_config(
    page_title="DIEMS Admission Assistant",
    page_icon="🎓",
    layout="centered",
)

st.title("🎓 DIEMS Admission Enquiry Chatbot")
st.caption(
    "Deogiri Institute of Engineering and Management Studies"
)

@st.cache_resource
def load_retriever():
    return DiemsRetriever()

try:
    retriever = load_retriever()
except Exception as exc:
    st.error(
        "The knowledge index could not be loaded. "
        "Check your dataset paths and indexing setup."
    )
    st.code(str(exc))
    st.stop()

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
                    answer = generate_answer(question, results)
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
