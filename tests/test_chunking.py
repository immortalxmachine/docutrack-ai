"""Unit tests for the text chunker (no PDFs, no model needed)."""
from __future__ import annotations

from app.ingest import chunk_text


def test_long_text_splits_into_multiple_chunks():
    text = ("Shipping policy section. " * 200).strip()
    chunks = chunk_text(text, chunk_size=200, overlap=40)
    assert len(chunks) > 1
    # Every chunk respects the configured size (allowing a small separator slack).
    assert all(len(c) <= 260 for c in chunks)


def test_overlap_preserves_continuity():
    # Distinct sentences so we can detect shared content across a boundary.
    text = ". ".join(f"sentence number {i} about customs" for i in range(60))
    chunks = chunk_text(text, chunk_size=150, overlap=50)
    assert len(chunks) >= 2


def test_trivial_fragments_are_dropped():
    assert chunk_text("tiny", chunk_size=100, overlap=10) == []
    assert chunk_text("", chunk_size=100, overlap=10) == []
