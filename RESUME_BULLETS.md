# DocuTrack AI — Résumé Bullets

Three bullets using only numbers measured from this repository (10 documents /
21 chunks, 30 eval questions, 100% hit-rate@3 & @5, 5 invoices, 4 REST
endpoints, 15 automated tests). Each ≤ 25 words.

- Built a retrieval-augmented Q&A service (FastAPI, FAISS, sentence-transformers)
  answering shipping-policy questions with file/page citations, achieving 100%
  retrieval hit-rate@3 across 30 evaluation questions.

- Engineered an LLM invoice-extraction endpoint parsing commercial-invoice PDFs
  into Pydantic-validated JSON, persisted via SQLAlchemy with SQL aggregate
  reporting across 5 test invoices.

- Added an anti-hallucination confidence guard and a switchable
  Gemini/Ollama/mock LLM provider, covered by 15 automated tests and
  ruff + pytest CI over 4 REST endpoints.
