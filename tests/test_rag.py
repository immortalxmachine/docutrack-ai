"""
Tests for the RAG answer logic, including the 'I don't know' confidence guard.

These use a hand-built FAISS store and a stubbed embedder, so the real
embedding model is never downloaded and the test is fully deterministic.
"""
from __future__ import annotations

import numpy as np

import app.rag as rag
from app.llm import MockProvider
from app.vectorstore import VectorStore


def _unit(vec: list[float]) -> np.ndarray:
    v = np.array([vec], dtype="float32")
    return v / np.linalg.norm(v)


def _store() -> VectorStore:
    store = VectorStore(dim=4)
    store.add(_unit([1, 0, 0, 0]), [{"file": "a.pdf", "page": 1, "text": "about A"}])
    store.add(_unit([0, 1, 0, 0]), [{"file": "b.pdf", "page": 2, "text": "about B"}])
    return store


def test_relevant_question_is_answered(monkeypatch):
    monkeypatch.setattr(rag, "embed_one", lambda q: _unit([1, 0, 0, 0]))
    resp = rag.answer_question("anything", llm=MockProvider(), store=_store())
    assert resp.answered is True
    assert resp.confidence > 0.9
    assert resp.citations[0].file == "a.pdf"


def test_irrelevant_question_returns_i_dont_know(monkeypatch):
    # Query orthogonal to every stored vector -> similarity ~0 -> below threshold.
    monkeypatch.setattr(rag, "embed_one", lambda q: _unit([0, 0, 1, 0]))
    resp = rag.answer_question("anything", llm=MockProvider(), store=_store())
    assert resp.answered is False
    assert resp.answer == rag.I_DONT_KNOW
    assert resp.confidence < 0.3
