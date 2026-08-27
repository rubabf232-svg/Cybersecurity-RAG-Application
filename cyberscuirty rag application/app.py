import streamlit as st

from rag_engine import RAGEngine


st.set_page_config(
    page_title="Cybersecurity RAG Assistant",
    page_icon="🛡️",
    layout="wide"
)


@st.cache_resource
def load_engine():
    return RAGEngine()


engine = load_engine()


st.title("🛡️ Cybersecurity RAG Assistant")

st.write(
    "Ask questions using the cybersecurity knowledge base."
)


with st.sidebar:

    st.header("📚 Knowledge Base")

    st.write(
        f"Documents loaded: "
        f"**{len(engine.documents)}**"
    )

    st.write(
        f"Knowledge chunks: "
        f"**{len(engine.chunks)}**"
    )

    st.divider()

    st.info(
        "Add .txt or .pdf files to the "
        "`knowledge` folder and restart the app."
    )


if "messages" not in st.session_state:
    st.session_state.messages = []


for message in st.session_state.messages:

    with st.chat_message(message["role"]):
        st.markdown(message["content"])

        if message.get("sources"):

            with st.expander("📚 Sources"):

                for source in message["sources"]:

                    st.write(
                        f"**{source['source']}** "
                        f"(Chunk {source['chunk_id']}) "
                        f"— Relevance: "
                        f"{source['score']}%"
                    )


question = st.chat_input(
    "Ask a cybersecurity question..."
)


if question:

    st.session_state.messages.append({
        "role": "user",
        "content": question
    })

    with st.chat_message("user"):
        st.markdown(question)

    result = engine.ask(
        question,
        top_k=4
    )

    sources = result["results"]

    with st.chat_message("assistant"):

        st.markdown(result["answer"])

        if sources:

            st.markdown("### 📚 Retrieved Sources")

            for source in sources:

                st.write(
                    f"**{source['source']}** — "
                    f"Chunk {source['chunk_id']} — "
                    f"{source['score']}% relevance"
                )

    st.session_state.messages.append({
        "role": "assistant",
        "content": result["answer"],
        "sources": sources
    })