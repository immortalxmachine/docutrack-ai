"""
FastAPI application — the public API surface.

Endpoints:
  GET  /health            liveness + which provider/index are active
  POST /ask               RAG question answering with citations
  POST /extract-invoice   PDF -> validated JSON -> stored in the DB
  GET  /invoices/summary  SQL aggregates over stored invoices

Run:  uvicorn app.main:app --reload
Docs: http://localhost:8000/docs
"""
from __future__ import annotations

import json
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, File, HTTPException, UploadFile

from app.config import get_settings
from app.db import init_db
from app.invoice import extract_invoice, save_invoice, summarize
from app.rag import answer_question
from app.schemas import (
    AskRequest,
    AskResponse,
    HealthResponse,
    InvoiceExtractResponse,
    InvoiceSummaryResponse,
)
from app.vectorstore import VectorStore


@asynccontextmanager
async def lifespan(_: FastAPI):
    # Create tables on boot so the first /extract-invoice call just works.
    init_db()
    yield


app = FastAPI(
    title="DocuTrack AI",
    description="RAG assistant for shipping & customs documents, plus invoice extraction.",
    version="0.1.0",
    lifespan=lifespan,
)


def _index_stats() -> tuple[bool, int]:
    """Cheaply report whether an index exists and how many chunks it holds."""
    index_dir = get_settings().index_dir
    meta_path = os.path.join(index_dir, "meta.json")
    if not VectorStore.exists(index_dir) or not os.path.exists(meta_path):
        return False, 0
    with open(meta_path, encoding="utf-8") as fh:
        return True, len(json.load(fh).get("metadata", []))


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    loaded, count = _index_stats()
    return HealthResponse(
        status="ok",
        llm_provider=get_settings().llm_provider,
        index_loaded=loaded,
        documents_indexed=count,
    )


@app.post("/ask", response_model=AskResponse)
def ask(req: AskRequest) -> AskResponse:
    try:
        return answer_question(req.question, top_k=req.top_k)
    except FileNotFoundError as exc:
        # No index built yet.
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@app.post("/extract-invoice", response_model=InvoiceExtractResponse)
async def extract_invoice_endpoint(file: UploadFile = File(...)) -> InvoiceExtractResponse:
    if not (file.filename or "").lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Please upload a PDF file.")
    from app.invoice import read_pdf_text

    text = read_pdf_text(await file.read())
    if not text:
        raise HTTPException(status_code=422, detail="Could not read any text from the PDF.")
    try:
        invoice = extract_invoice(text)
    except Exception as exc:  # JSON parse / Pydantic validation failures
        raise HTTPException(status_code=422, detail=f"Extraction failed: {exc}") from exc
    saved_id = save_invoice(invoice)
    return InvoiceExtractResponse(invoice=invoice, saved_id=saved_id)


@app.get("/invoices/summary", response_model=InvoiceSummaryResponse)
def invoices_summary() -> InvoiceSummaryResponse:
    return summarize()
