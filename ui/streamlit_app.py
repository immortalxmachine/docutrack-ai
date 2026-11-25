"""
Streamlit chat UI for DocuTrack AI.

A thin client: it only calls the FastAPI backend over HTTP and renders the
answer plus each citation as an expandable source. Point it at the API with
API_BASE_URL (defaults to http://localhost:8000).

Run:  streamlit run ui/streamlit_app.py
"""
from __future__ import annotations

import os

import requests
import streamlit as st

API_BASE = os.environ.get("API_BASE_URL", "http://localhost:8000")

st.set_page_config(page_title="DocuTrack AI", page_icon="📦", layout="centered")
st.title("📦 DocuTrack AI")
st.caption("Ask about shipping & customs policies. Answers cite the source document and page.")

# --- Sidebar: backend health -------------------------------------------------
with st.sidebar:
    st.header("Backend")
    st.write(f"API: `{API_BASE}`")
    try:
        h = requests.get(f"{API_BASE}/health", timeout=5).json()
        st.success("Connected")
        st.write(f"LLM provider: **{h['llm_provider']}**")
        st.write(f"Index loaded: **{h['index_loaded']}**")
        st.write(f"Chunks indexed: **{h['documents_indexed']}**")
    except Exception as exc:  # backend down
        st.error(f"Backend unreachable: {exc}")

    st.divider()
    st.subheader("Invoice summary")
    if st.button("Load summary"):
        try:
            s = requests.get(f"{API_BASE}/invoices/summary", timeout=10).json()
            st.metric("Invoices stored", s["total_invoices"])
            st.metric("Total declared value", f"{s['total_declared_value']:,.2f}")
            st.write("By destination country:")
            st.table(s["by_destination_country"])
            st.write("Top HS codes:")
            st.table(s["top_hs_codes"])
        except Exception as exc:
            st.error(f"Could not load summary: {exc}")

# --- Chat history ------------------------------------------------------------
if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        for c in msg.get("citations", []):
            with st.expander(f"Source: {c['file']} — page {c['page']}  (score {c['score']})"):
                st.write(f"From **{c['file']}**, page {c['page']}.")

# --- Chat input --------------------------------------------------------------
if question := st.chat_input("Ask a shipping or customs question..."):
    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)

    with st.chat_message("assistant"):
        try:
            resp = requests.post(f"{API_BASE}/ask", json={"question": question}, timeout=120)
            resp.raise_for_status()
            data = resp.json()
            answer = data["answer"]
            citations = data["citations"] if data["answered"] else []
            st.markdown(answer)
            if not data["answered"]:
                st.info("Low retrieval confidence — the assistant declined to guess.")
            for c in citations:
                with st.expander(f"Source: {c['file']} — page {c['page']}  (score {c['score']})"):
                    st.write(f"From **{c['file']}**, page {c['page']}.")
            st.session_state.messages.append(
                {"role": "assistant", "content": answer, "citations": citations}
            )
        except Exception as exc:
            st.error(f"Request failed: {exc}")
