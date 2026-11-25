# DocuTrack AI

> A Generative-AI assistant for shipping & customs documents: ask questions
> against a library of policy PDFs and get answers **with citations**, and
> extract structured data from commercial invoices into a database.

**Status:** under active construction. Metrics in this README are filled in
only after the code is actually run — no invented numbers.

---

## What it does

1. **Document Q&A (RAG):** a FastAPI `/ask` endpoint retrieves the most
   relevant chunks from a FAISS vector index of shipping-policy PDFs and asks
   an LLM to answer *using only those chunks*, returning the source file and
   page for every answer. Low-confidence retrievals return "I don't know"
   instead of guessing.
2. **Invoice extraction:** `/extract-invoice` turns a commercial-invoice PDF
   into validated JSON (shipper, consignee, HS codes, line items, declared
   value) and stores it in a SQL database; `/invoices/summary` runs SQL
   aggregates over everything extracted.

> All documents in `data/docs/` are **synthetic samples** created for this
> project; each carries a "Synthetic sample document" footer.

## Tech stack

Python 3.11 · FastAPI · LangChain (text splitting) · sentence-transformers
(`all-MiniLM-L6-v2`) · FAISS · Google Gemini / Ollama (switchable) ·
SQLAlchemy + PostgreSQL · Streamlit · Docker · GitHub Actions

## Architecture

_Mermaid diagram added in the docs step._

## How to run

_Filled in once the services are wired up._

## Evaluation

_Retrieval hit-rate@3 / @5 filled in from `eval/results.json` after running
`python -m eval.run_eval`._

---
See [`INTERVIEW_NOTES.md`](INTERVIEW_NOTES.md) and
[`RESUME_BULLETS.md`](RESUME_BULLETS.md).
