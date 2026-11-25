"""
Invoice extraction and summary.

  * extract_invoice(): send the invoice text to the LLM with a strict schema,
    parse the JSON it returns, and validate it with Pydantic. Validation is the
    safety net — a malformed LLM response raises instead of writing junk to the DB.
  * save_invoice(): persist the validated invoice and its line items.
  * summarize(): run SQL aggregates (total declared value by country, top HS codes).
"""
from __future__ import annotations

import io
import json
import re

from sqlalchemy import func, select

from app.db import Invoice, LineItem, get_session
from app.llm import LLMProvider, get_llm
from app.schemas import (
    CountryTotal,
    HsCodeCount,
    InvoiceData,
    InvoiceSummaryResponse,
)

EXTRACTION_SYSTEM = (
    "You extract structured data from commercial invoices. "
    "Return ONLY a single JSON object, no prose, no markdown fences. "
    "Use null for any field you cannot find. Numbers must be plain numbers."
)

EXTRACTION_TEMPLATE = """Extract the following fields from this commercial invoice and return JSON with exactly this shape:
{{
  "invoice_number": string|null,
  "invoice_date": string|null,
  "currency": string|null,
  "shipper": {{"name": string, "address": string|null, "country": string|null}},
  "consignee": {{"name": string, "address": string|null, "country": string|null}},
  "line_items": [{{"description": string, "hs_code": string|null, "quantity": number|null, "unit_price": number|null, "amount": number|null}}],
  "declared_value": number
}}

INVOICE TEXT:
{text}
"""


def read_pdf_text(data: bytes) -> str:
    """Extract all text from an uploaded PDF (bytes)."""
    from pypdf import PdfReader

    reader = PdfReader(io.BytesIO(data))
    return "\n".join((page.extract_text() or "") for page in reader.pages).strip()


def _parse_json(raw: str) -> dict:
    """Pull the first JSON object out of the LLM response, tolerating fences."""
    raw = raw.strip()
    raw = re.sub(r"^```(?:json)?|```$", "", raw, flags=re.MULTILINE).strip()
    match = re.search(r"\{.*\}", raw, flags=re.DOTALL)
    if not match:
        raise ValueError("LLM response contained no JSON object.")
    return json.loads(match.group(0))


def extract_invoice(pdf_text: str, llm: LLMProvider | None = None) -> InvoiceData:
    """Extract and validate an invoice from its text."""
    llm = llm or get_llm()
    raw = llm.generate(EXTRACTION_TEMPLATE.format(text=pdf_text), system=EXTRACTION_SYSTEM)
    data = _parse_json(raw)

    # If the model omitted the total, derive it from the line items.
    if not data.get("declared_value"):
        data["declared_value"] = sum(
            (it.get("amount") or 0) for it in data.get("line_items", [])
        )

    return InvoiceData.model_validate(data)   # raises on a bad shape


def save_invoice(invoice: InvoiceData) -> int:
    """Persist a validated invoice and return its new primary key."""
    session = get_session()
    try:
        row = Invoice(
            invoice_number=invoice.invoice_number,
            invoice_date=invoice.invoice_date,
            currency=invoice.currency,
            shipper_name=invoice.shipper.name,
            shipper_country=invoice.shipper.country,
            consignee_name=invoice.consignee.name,
            consignee_country=invoice.consignee.country,
            declared_value=invoice.declared_value,
            line_items=[
                LineItem(
                    description=li.description,
                    hs_code=li.hs_code,
                    quantity=li.quantity,
                    unit_price=li.unit_price,
                    amount=li.amount,
                )
                for li in invoice.line_items
            ],
        )
        session.add(row)
        session.commit()
        return row.id
    finally:
        session.close()


def summarize() -> InvoiceSummaryResponse:
    """Run SQL aggregates over all stored invoices."""
    session = get_session()
    try:
        total_invoices = session.scalar(select(func.count(Invoice.id))) or 0
        total_value = session.scalar(select(func.coalesce(func.sum(Invoice.declared_value), 0.0))) or 0.0

        # Total declared value grouped by destination (consignee) country.
        country_rows = session.execute(
            select(
                Invoice.consignee_country,
                func.count(Invoice.id),
                func.coalesce(func.sum(Invoice.declared_value), 0.0),
            )
            .group_by(Invoice.consignee_country)
            .order_by(func.sum(Invoice.declared_value).desc())
        ).all()

        # Most frequent HS codes across all line items.
        hs_rows = session.execute(
            select(LineItem.hs_code, func.count(LineItem.id))
            .where(LineItem.hs_code.is_not(None))
            .group_by(LineItem.hs_code)
            .order_by(func.count(LineItem.id).desc())
            .limit(10)
        ).all()

        return InvoiceSummaryResponse(
            total_invoices=total_invoices,
            total_declared_value=round(float(total_value), 2),
            by_destination_country=[
                CountryTotal(
                    country=c or "Unknown",
                    invoice_count=n,
                    total_declared_value=round(float(v), 2),
                )
                for c, n, v in country_rows
            ],
            top_hs_codes=[HsCodeCount(hs_code=h, line_item_count=n) for h, n in hs_rows],
        )
    finally:
        session.close()
