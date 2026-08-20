import streamlit as st

from demo.config import RAG_SIMILARITY_HIGH, RAG_SIMILARITY_MEDIUM, get_mode_label
from demo.helpers.ui_status import render_service_error
from demo.services.service_client import ask_rag
from demo.services.service_errors import is_error


def _similarity_badge(score: float) -> str:
    percentage = round(score * 100)
    if score >= RAG_SIMILARITY_HIGH:
        return f":green[High Relevance ({percentage}%)]"
    elif score >= RAG_SIMILARITY_MEDIUM:
        return f":orange[Medium Relevance ({percentage}%)]"
    elif score >= 0.50:
        return f":red[Low Relevance ({percentage}%)]"
    else:
        return f":red[🔴 Low Relevance ({percentage}%)]"


def _render_citations(citations, retrieved_context):
    if not citations:
        return

    context_by_chunk = {
        ctx.get("chunk_id"): ctx for ctx in (retrieved_context or [])
    }

    st.markdown("##### 📌 Citations")
    cit_cols = st.columns(len(citations))
    for idx, cite in enumerate(citations):
        chunk_id = cite.get("chunk_id", "")
        ctx = context_by_chunk.get(chunk_id, {})
        score = ctx.get("similarity_score", 0.0)

        with cit_cols[idx]:
            # Render HTML card with document_external_id and document_db_id
            st.markdown(
                f"""
                <div style="background-color: #f1f5f9; border: 1px solid #cbd5e1; padding: 8px; border-radius: 6px; font-size: 13px; min-height: 90px; margin-bottom: 10px;">
                    📄 <strong>{cite.get('file_name', 'Source')}</strong><br/>
                    Page {cite.get('page_number', 'N/A')}<br/>
                    <span style="font-size: 10px; color: #475569;">Chunk: {chunk_id}</span><br/>
                    <span style="font-size: 10px; color: #475569;">Ext ID: {cite.get('document_external_id', 'N/A')}</span><br/>
                    <span style="font-size: 10px; color: #475569;">DB ID: {cite.get('document_db_id', 'N/A')}</span>
                </div>
                """,
                unsafe_allow_html=True
            )
            # Render expander for text & score right inside the column
            with st.expander("🔍 Preview Context"):
                st.markdown(_similarity_badge(score))
                if ctx.get("chunk_text"):
                    text = ctx["chunk_text"]
                    preview = text[:300] + ("..." if len(text) > 300 else "")
                    st.write(preview)
                else:
                    st.caption("Context text not available.")


def main():
    """Render RAG chatbot page, backed by service_client."""
    st.title("💬 QS Chatbot")
    st.caption(f"Data mode: {get_mode_label()}")
    st.markdown(
        "Ask a question about your ingested documents. Answers are grounded "
        "in retrieved context with source citations."
    )
    st.markdown("---")

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = [
            {
                "role": "assistant",
                "message": "Hello, I'm QS. Ask me anything about your data, files, or analysis results.",
            },
        ]

    st.caption("Tip: Press Enter to send your message.")

    for chat in st.session_state.chat_history:
        with st.chat_message(chat["role"]):
            if chat.get("error_response"):
                render_service_error(
                    chat["error_response"],
                    "RAG service",
                    what_is_missing=(
                        "No answer and no citations were returned. Do not treat "
                        "this turn as a retrieval result."
                    ),
                )
                continue
            st.markdown(chat["message"])
            if chat.get("citations"):
                _render_citations(chat["citations"], chat.get("retrieved_context"))
            if chat.get("status") == "no_match":
                st.info("No relevant content found.")
            if chat.get("model"):
                st.caption(f"🤖 **Model:** `{chat['model']}`")
            if chat.get("retrieval_backend"):
                st.caption(
                    f"Retrieval backend: `{chat['retrieval_backend']}` | "
                    f"Embedding dimension: `{chat.get('embedding_dimension', 'N/A')}`"
                )

    user_input = st.chat_input("Message QS...")

    if user_input:
        st.session_state.chat_history.append({"role": "user", "message": user_input})

        document_id = st.session_state.get("selected_document_id")
        response = ask_rag(user_input, document_id=document_id)

        if is_error(response):
            # Never store a failed retrieval as RAG context: downstream
            # suggestions and reports must not cite an answer that never came.
            st.session_state["last_rag_response"] = {}
            st.session_state.chat_history.append({
                "role": "assistant",
                "message": "",
                "error_response": response,
            })
            st.rerun()

        st.session_state["last_rag_response"] = response.get("data", {})
        data = response.get("data", {})

        st.session_state.chat_history.append({
            "role": "assistant",
            "message": data.get(
                "answer", "I do not know based on the provided documents."
            ),
            "citations": data.get("citations", []),
            "retrieved_context": data.get("retrieved_context", []),
            "model": data.get("model", ""),
            "retrieval_backend": data.get("retrieval_backend", ""),
            "embedding_dimension": data.get("embedding_dimension"),
            "status": data.get("status", ""),
        })
        st.rerun()


if __name__ == "__main__":
    main()
