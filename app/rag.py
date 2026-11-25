"""
Retrieval-Augmented Generation.

Flow of /ask:
  1. Embed the question and retrieve the top-k most similar chunks from FAISS.
  2. If the best similarity is below MIN_CONFIDENCE, return "I don't know"
     WITHOUT calling the LLM. This is the anti-hallucination guard: if nothing
     in the corpus is relevant, we refuse rather than invent an answer.
  3. Otherwise build a prompt containing only the retrieved chunks and a strict
     instruction to answer from them alone, then call the LLM.
  4. Return the answer with a citation (file + page) for every chunk used.
"""
from __future__ import annotations

from functools import lru_cache

from app.config import get_settings
from app.embeddings import embed_one
from app.llm import LLMProvider, get_llm
from app.schemas import AskResponse, Citation
from app.vectorstore import VectorStore

SYSTEM_PROMPT = (
    "You are DocuTrack, an assistant for shipping and customs questions. "
    "Answer ONLY using the numbered context passages provided. "
    "If the answer is not contained in the context, reply exactly: "
    "\"I don't know based on the available documents.\" "
    "Be concise and cite nothing yourself; the system adds citations."
)

I_DONT_KNOW = "I don't know based on the available documents."


@lru_cache
def _store() -> VectorStore:
    """Load and cache the FAISS index once per process."""
    return VectorStore.load(get_settings().index_dir)


def _build_prompt(question: str, contexts: list[dict]) -> str:
    """Assemble the user prompt: numbered context passages + the question."""
    blocks = []
    for n, c in enumerate(contexts, start=1):
        blocks.append(f"[{n}] (source: {c['file']}, page {c['page']})\n{c['text']}")
    joined = "\n\n".join(blocks)
    return f"Context passages:\n{joined}\n\nQuestion: {question}\n\nAnswer:"


def answer_question(
    question: str,
    top_k: int | None = None,
    llm: LLMProvider | None = None,
    store: VectorStore | None = None,
) -> AskResponse:
    """Answer a question against the indexed documents.

    `llm` and `store` are injectable so tests can pass mocks without touching
    the real model or index.
    """
    settings = get_settings()
    k = top_k or settings.top_k
    store = store or _store()

    hits = store.search(embed_one(question), k)
    if not hits:
        return AskResponse(answer=I_DONT_KNOW, citations=[], confidence=0.0, answered=False)

    best_score = hits[0][1]
    citations = [Citation(file=m["file"], page=m["page"], score=round(s, 4)) for m, s in hits]

    # Anti-hallucination guard: refuse when nothing is relevant enough.
    if best_score < settings.min_confidence:
        return AskResponse(answer=I_DONT_KNOW, citations=citations,
                           confidence=round(best_score, 4), answered=False)

    llm = llm or get_llm(settings)
    prompt = _build_prompt(question, [m for m, _ in hits])
    answer = llm.generate(prompt, system=SYSTEM_PROMPT).strip()

    answered = I_DONT_KNOW.lower() not in answer.lower()
    return AskResponse(answer=answer, citations=citations,
                       confidence=round(best_score, 4), answered=answered)
