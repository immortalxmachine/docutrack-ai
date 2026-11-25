"""
Pydantic models — the validated contract for every API request and response.

Keeping these in one file makes the API shape easy to read and gives the
invoice-extraction step a strict schema the LLM output must conform to.
"""
from __future__ import annotations

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# RAG Q&A
# ---------------------------------------------------------------------------
class AskRequest(BaseModel):
    question: str = Field(..., min_length=3, max_length=1000,
                          description="The user's natural-language question.")
    top_k: int | None = Field(None, ge=1, le=10,
                              description="Override how many chunks to retrieve.")


class Citation(BaseModel):
    file: str = Field(..., description="Source PDF file name.")
    page: int = Field(..., description="1-based page number the chunk came from.")
    score: float = Field(..., description="Cosine similarity of the chunk to the question.")


class AskResponse(BaseModel):
    answer: str
    citations: list[Citation]
    confidence: float = Field(..., description="Similarity of the best-matching chunk.")
    answered: bool = Field(..., description="False when confidence < threshold ('I don't know').")


# ---------------------------------------------------------------------------
# Invoice extraction
# ---------------------------------------------------------------------------
class InvoiceParty(BaseModel):
    name: str
    address: str | None = None
    country: str | None = None


class InvoiceLineItem(BaseModel):
    description: str
    hs_code: str | None = Field(None, description="Harmonised System tariff code.")
    quantity: float | None = None
    unit_price: float | None = None
    amount: float | None = None


class InvoiceData(BaseModel):
    """The structured form of a commercial invoice.

    Every field is optional except the two parties and the declared value, so
    extraction still succeeds (with nulls) on an imperfect source document
    rather than throwing the whole result away.
    """

    invoice_number: str | None = None
    invoice_date: str | None = None
    currency: str | None = None
    shipper: InvoiceParty
    consignee: InvoiceParty
    line_items: list[InvoiceLineItem] = Field(default_factory=list)
    declared_value: float = Field(..., description="Total declared value of the shipment.")


class InvoiceExtractResponse(BaseModel):
    invoice: InvoiceData
    saved_id: int = Field(..., description="Primary key of the stored invoice row.")


# ---------------------------------------------------------------------------
# Invoice summary (SQL aggregates)
# ---------------------------------------------------------------------------
class CountryTotal(BaseModel):
    country: str
    invoice_count: int
    total_declared_value: float


class HsCodeCount(BaseModel):
    hs_code: str
    line_item_count: int


class InvoiceSummaryResponse(BaseModel):
    total_invoices: int
    total_declared_value: float
    by_destination_country: list[CountryTotal]
    top_hs_codes: list[HsCodeCount]


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------
class HealthResponse(BaseModel):
    status: str
    llm_provider: str
    index_loaded: bool
    documents_indexed: int
