"""
Ingestion pipeline: PDFs -> text -> chunks -> embeddings -> FAISS index.

Steps (run with `python -m app.ingest`):
  1. Read every PDF in DOCS_DIR, one page at a time (pypdf) so each chunk keeps
     the page it came from — that page number is what /ask cites.
  2. Split each page with LangChain's RecursiveCharacterTextSplitter, which
     tries to break on paragraph/line boundaries before falling back to raw
     character cuts, with a configurable overlap so a fact split across a
     boundary still appears whole in at least one chunk.
  3. Embed all chunks and store them in a FAISS index with {file, page, text}.
"""
from __future__ import annotations

import glob
import os

from langchain_text_splitters import RecursiveCharacterTextSplitter
from pypdf import PdfReader

from app.config import get_settings
from app.embeddings import dimension, embed
from app.vectorstore import VectorStore


def _load_pages(pdf_path: str) -> list[tuple[int, str]]:
    """Return [(page_number, text)] for a PDF; page numbers are 1-based."""
    reader = PdfReader(pdf_path)
    pages: list[tuple[int, str]] = []
    for i, page in enumerate(reader.pages, start=1):
        text = (page.extract_text() or "").strip()
        if text:
            pages.append((i, text))
    return pages


def chunk_text(text: str, chunk_size: int, overlap: int) -> list[str]:
    """Split one page of text into overlapping chunks.

    Pulled out as a pure function so it can be unit-tested without any PDFs.
    Fragments shorter than 30 characters are dropped as noise.
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=overlap,
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    return [p.strip() for p in splitter.split_text(text) if len(p.strip()) >= 30]


def _chunk_documents(docs_dir: str, chunk_size: int, overlap: int) -> list[dict]:
    """Walk every PDF and return a flat list of chunk dicts {file, page, text}."""
    chunks: list[dict] = []
    pdf_paths = sorted(glob.glob(os.path.join(docs_dir, "*.pdf")))
    if not pdf_paths:
        raise FileNotFoundError(
            f"No PDFs in '{docs_dir}'. Run: python -m scripts.fetch_docs"
        )
    for path in pdf_paths:
        fname = os.path.basename(path)
        for page_no, page_text in _load_pages(path):
            for piece in chunk_text(page_text, chunk_size, overlap):
                chunks.append({"file": fname, "page": page_no, "text": piece})
    return chunks


def build_index() -> VectorStore:
    """Build the FAISS index from the document library and persist it."""
    settings = get_settings()
    print(f"Chunking PDFs in {settings.docs_dir}/ ...")
    chunks = _chunk_documents(settings.docs_dir, settings.chunk_size, settings.chunk_overlap)
    print(f"  -> {len(chunks)} chunks")

    print(f"Embedding with {settings.embedding_model} ...")
    vectors = embed([c["text"] for c in chunks])

    store = VectorStore(dim=dimension())
    store.add(vectors, chunks)
    store.save(settings.index_dir)
    print(f"Saved FAISS index ({store.size} vectors, dim {store.dim}) to {settings.index_dir}/")
    return store


if __name__ == "__main__":
    build_index()
