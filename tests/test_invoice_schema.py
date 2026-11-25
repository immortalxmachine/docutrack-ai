"""Tests for invoice JSON parsing and Pydantic validation."""
from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.invoice import _parse_json, extract_invoice
from app.schemas import InvoiceData


class _FakeLLM:
    """Returns a fixed JSON string, standing in for a real model."""

    def __init__(self, payload: str) -> None:
        self._payload = payload

    def generate(self, prompt: str, system: str | None = None) -> str:
        return self._payload


def test_valid_invoice_validates():
    inv = InvoiceData.model_validate({
        "shipper": {"name": "A", "country": "India"},
        "consignee": {"name": "B", "country": "USA"},
        "declared_value": 100.0,
        "line_items": [{"description": "widgets", "hs_code": "123456", "quantity": 2, "unit_price": 5}],
    })
    assert inv.declared_value == 100.0
    assert inv.line_items[0].hs_code == "123456"


def test_missing_declared_value_is_rejected():
    with pytest.raises(ValidationError):
        InvoiceData.model_validate({
            "shipper": {"name": "A"},
            "consignee": {"name": "B"},
        })


def test_parse_json_strips_markdown_fences():
    raw = "```json\n{\"a\": 1}\n```"
    assert _parse_json(raw) == {"a": 1}


def test_parse_json_without_object_raises():
    with pytest.raises(ValueError):
        _parse_json("no json here")


def test_extract_invoice_computes_missing_total():
    payload = (
        '{"shipper": {"name": "S", "country": "India"},'
        ' "consignee": {"name": "C", "country": "UK"},'
        ' "currency": "USD",'
        ' "line_items": [{"description": "x", "amount": 40}, {"description": "y", "amount": 60}]}'
    )
    inv = extract_invoice("ignored text", llm=_FakeLLM(payload))
    assert inv.declared_value == 100.0        # derived from line-item amounts
    assert inv.consignee.country == "UK"
