# DocuTrack AI — Résumé Bullets

Three bullets using only numbers measured from this repository (10 real
public-domain U.S. government documents / 1,842 chunks, 28 eval questions, 96.4%
hit-rate@3 & @5, 5 sample invoices, 4 REST endpoints, 15 automated tests). Each
≤ 25 words.

- Built a retrieval-augmented Q&A service (FastAPI, FAISS, sentence-transformers)
  over 1,842 chunks from 10 public-domain CBP/Census/CFR documents, returning
  file/page citations at 96% retrieval hit-rate across 28 evaluation questions.

- Engineered an LLM invoice-extraction endpoint parsing commercial-invoice PDFs
  into Pydantic-validated JSON, persisted via SQLAlchemy with SQL aggregate
  reporting across 5 sample invoices.

- Added an anti-hallucination confidence guard and a switchable
  Gemini/Ollama/mock LLM provider, covered by 15 automated tests and
  ruff + pytest CI over 4 REST endpoints.
