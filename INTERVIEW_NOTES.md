# DocuTrack AI — Interview Notes

Twenty questions an interviewer is likely to ask about **this exact code**,
with answers and the file/function where each concept lives. Numbers (hit-rate,
chunk counts) come from running `python -m eval.run_eval` — see the README.

---

### 1. What is RAG and why use it here?
Retrieval-Augmented Generation: instead of relying on the LLM's trained
knowledge, we **retrieve** relevant passages from our own documents and give
them to the model as context, so answers are grounded in *our* policies and can
be cited. Lives in `app/rag.py → answer_question()`. It solves two problems:
the model has never seen our private policies, and we need traceable citations.

### 2. Walk me through the full flow of a `/ask` request.
`app/main.py → ask()` calls `app/rag.py → answer_question()`, which: (1) embeds
the question (`app/embeddings.py → embed_one`), (2) searches FAISS
(`app/vectorstore.py → search`), (3) checks the top similarity against
`MIN_CONFIDENCE`, (4) builds a context-only prompt (`_build_prompt`), (5) calls
the LLM (`app/llm.py`), and (6) returns the answer with one citation per chunk.

### 3. What are embeddings?
Dense vectors that place semantically similar text near each other. We use
`sentence-transformers/all-MiniLM-L6-v2` (384 dimensions) — small, fast, and
good enough for short policy passages. See `app/embeddings.py`. Vectors are
**L2-normalised** so an inner-product search equals cosine similarity.

### 4. Why normalise embeddings and use `IndexFlatIP`?
If every vector has length 1, the dot product between two vectors *is* their
cosine similarity. So we normalise at embed time (`normalize_embeddings=True`)
and use FAISS `IndexFlatIP` (inner product). `app/embeddings.py`,
`app/vectorstore.py → __init__`.

### 5. Why `IndexFlatIP` (brute force) instead of an approximate index like IVF/HNSW?
`IndexFlatIP` is exact and needs no training or tuning. Our corpus is only a few
hundred chunks, where brute force is already instant. Approximate indexes (IVF,
HNSW) trade a little recall for speed and matter at millions of vectors — I'd
switch then. This is a deliberate "simplest thing that is correct" choice.

### 6. How does chunking work and what are the trade-offs of chunk size?
`app/ingest.py → chunk_text()` uses LangChain's `RecursiveCharacterTextSplitter`
(≈800 chars, 120 overlap). **Too large** → each chunk mixes several topics, so
retrieval is less precise and you waste context tokens. **Too small** → a single
fact gets split and loses surrounding meaning. **Overlap** ensures a fact sitting
on a boundary still appears whole in at least one chunk.

### 7. Why split per page, not per document?
`app/ingest.py → _load_pages()` reads each PDF page separately so every chunk
keeps the page number it came from — that page is what `/ask` cites. Chunking a
whole document would lose the page provenance.

### 8. How do you prevent hallucinations?
Two guards in `app/rag.py`: (1) a **confidence threshold** — if the best
retrieved similarity is below `MIN_CONFIDENCE` we return "I don't know" *without
ever calling the LLM*; (2) a **strict system prompt** (`SYSTEM_PROMPT`) telling
the model to answer only from the supplied context and otherwise say it doesn't
know. We also set `answered=False` so the UI can flag low-confidence replies.

### 9. How did you design the prompt?
`SYSTEM_PROMPT` sets the role and the "answer only from context / else say I
don't know" rule. The user prompt (`_build_prompt`) lists numbered passages each
tagged with its source file and page, then the question. Numbering makes it easy
for the model to ground its answer and for us to attach citations.

### 10. What does Pydantic do in this project?
Three jobs: (1) validates API request/response shapes (`app/schemas.py`,
e.g. `AskRequest` enforces question length); (2) validates **LLM output** for
invoice extraction — `InvoiceData.model_validate()` in `app/invoice.py` rejects
a malformed JSON object before it reaches the database; (3) `pydantic-settings`
loads typed config from env (`app/config.py`).

### 11. How does invoice extraction turn a PDF into structured data?
`app/invoice.py`: `read_pdf_text()` (pypdf) → a strict prompt asking for a JSON
object with an exact shape (`EXTRACTION_TEMPLATE`) → `_parse_json()` tolerates
markdown fences and extracts the first `{...}` → `InvoiceData.model_validate()`
validates it. If the model omits the total, we derive it from the line items.

### 12. What SQL do you actually run?
`app/invoice.py → summarize()` runs SQLAlchemy Core aggregates: a `COUNT` and
`SUM(declared_value)` overall; a `GROUP BY consignee_country` with
`SUM(...) ORDER BY ... DESC` for value by destination; and a
`GROUP BY hs_code ... ORDER BY COUNT(*) DESC LIMIT 10` for the top HS codes.

### 13. Why SQLAlchemy, and why does the same code run on SQLite and Postgres?
SQLAlchemy abstracts the database behind one API, so only the `DATABASE_URL`
changes between a zero-setup local SQLite file and Postgres in docker-compose.
Models in `app/db.py`; the engine is built from the URL in `_make_engine()`.

### 14. How is the LLM provider made switchable?
`app/llm.py` defines an abstract `LLMProvider.generate()` with three
implementations (Gemini, Ollama, Mock). `get_llm()` picks one from
`LLM_PROVIDER`. No other module imports a vendor SDK, so swapping providers is a
one-line config change. The `mock` provider is offline and deterministic — it's
what CI and keyless demos use.

### 15. How do you test an app that depends on an LLM and an embedding model?
We never call either in tests. `tests/conftest.py` forces `LLM_PROVIDER=mock`.
`tests/test_rag.py` injects a hand-built FAISS store and stubs the embedder, so
the confidence guard is tested deterministically. `tests/test_api.py` uses
FastAPI's `TestClient` with the mock provider. This keeps CI fast and free.

### 16. What exactly does the evaluation measure?
`eval/run_eval.py` measures **retrieval** only (no LLM): for 28 questions with a
known source document, it computes **hit-rate@3** and **hit-rate@5** — the
fraction of questions whose correct document appears in the top-3 / top-5
retrieved chunks. Deterministic and cheap to reproduce. On the real corpus
(1,842 chunks from 10 public-domain documents) it scores 96.4% (27/28); the one
miss is a near-duplicate between the two Census export documents (FTR vs AES
Quick Guide).

### 17. Why evaluate retrieval separately from generation?
Most RAG failures are retrieval failures: if the right passage isn't retrieved,
no prompt can save the answer. Measuring retrieval in isolation tells me whether
to tune chunking/embeddings versus the prompt. It's also objective and needs no
human grading.

### 18. What would you do if hit-rate were low?
Tune chunk size/overlap, try a stronger embedding model, add query
pre-processing, or use hybrid search (BM25 keyword + vector) and re-ranking.
Because `eval/run_eval.py` is deterministic I can measure each change.

### 19. Why FastAPI, and what does `/health` give you?
FastAPI gives typed request/response models (shared with Pydantic),
auto-generated OpenAPI docs at `/docs`, and async file uploads for
`/extract-invoice`. `/health` reports the active provider and whether the index
is loaded — useful for container orchestration and the UI's status panel.

### 20. How would you take this to production / scale it?
Pre-build and ship the FAISS index (or move to a managed vector DB like pgvector
or Pinecone) rather than rebuilding on boot; cache embeddings; add auth and rate
limiting; stream LLM responses; add observability (latency, hit-rate,
"I don't know" rate); and run the eval in CI as a quality gate.

---

### Things most likely to be grilled on
1. **The confidence guard** (`app/rag.py`): be ready to explain the exact
   threshold behaviour and why refusing is better than guessing.
2. **Normalisation ↔ cosine ↔ IndexFlatIP** (questions 4–5): the one-line reason
   normalised dot product equals cosine similarity.
3. **Pydantic validating LLM output** (question 10/11): why validating the
   model's JSON before the DB write is the safety net that makes the feature
   trustworthy.
