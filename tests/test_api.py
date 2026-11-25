"""
API tests using FastAPI's TestClient and the offline 'mock' LLM provider.

Covers /health, the invoice extraction + storage + summary path, and the
/ask behaviour when no index is present.
"""
from __future__ import annotations

import io

from fastapi.testclient import TestClient
from reportlab.pdfgen import canvas

from app.main import app

client = TestClient(app)


def _tiny_pdf() -> bytes:
    """Produce a minimal one-page PDF in memory (content is irrelevant: the
    mock LLM returns a fixed JSON regardless)."""
    buf = io.BytesIO()
    c = canvas.Canvas(buf)
    c.drawString(72, 720, "Commercial Invoice INV-TEST-1")
    c.drawString(72, 700, "Shipper: Test Exporter, India")
    c.save()
    buf.seek(0)
    return buf.read()


def test_health_reports_mock_provider():
    resp = client.get("/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert body["llm_provider"] == "mock"


def test_ask_without_index_returns_503():
    resp = client.post("/ask", json={"question": "What is the re-packaging surcharge?"})
    assert resp.status_code == 503


def test_ask_rejects_too_short_question():
    resp = client.post("/ask", json={"question": "a"})
    assert resp.status_code == 422   # fails AskRequest min_length validation


def test_extract_invoice_and_summary():
    files = {"file": ("invoice.pdf", _tiny_pdf(), "application/pdf")}
    resp = client.post("/extract-invoice", files=files)
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert isinstance(body["saved_id"], int)
    assert "invoice" in body

    summary = client.get("/invoices/summary")
    assert summary.status_code == 200
    assert summary.json()["total_invoices"] >= 1


def test_extract_invoice_rejects_non_pdf():
    files = {"file": ("note.txt", b"hello", "text/plain")}
    resp = client.post("/extract-invoice", files=files)
    assert resp.status_code == 400
