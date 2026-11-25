"""
LLM provider abstraction.

One tiny interface (`LLMProvider.generate`) with three implementations chosen
by the LLM_PROVIDER setting:

  * gemini — Google Gemini free tier (needs GEMINI_API_KEY)
  * ollama — a local model served by Ollama (no API key, no internet)
  * mock   — deterministic, offline; used by the test suite and for a
             zero-setup local demo. Never calls a network.

Keeping the LLM behind this interface is what makes the provider "switchable
in config": no retrieval or API code imports a vendor SDK directly.
"""
from __future__ import annotations

import json
from abc import ABC, abstractmethod

import requests

from app.config import Settings, get_settings


class LLMProvider(ABC):
    """Minimal text-in / text-out interface every provider implements."""

    @abstractmethod
    def generate(self, prompt: str, system: str | None = None) -> str:
        """Return the model's completion for `prompt` (with optional system text)."""
        raise NotImplementedError


class GeminiProvider(LLMProvider):
    """Google Gemini via the google-generativeai SDK."""

    def __init__(self, settings: Settings) -> None:
        if not settings.gemini_api_key:
            raise RuntimeError(
                "LLM_PROVIDER=gemini but GEMINI_API_KEY is empty. "
                "Set it in .env or switch LLM_PROVIDER to 'ollama' or 'mock'."
            )
        import google.generativeai as genai  # imported lazily so mock/ollama need no SDK

        genai.configure(api_key=settings.gemini_api_key)
        self._model = genai.GenerativeModel(settings.gemini_model)

    def generate(self, prompt: str, system: str | None = None) -> str:
        full = f"{system}\n\n{prompt}" if system else prompt
        resp = self._model.generate_content(full)
        return (resp.text or "").strip()


class OllamaProvider(LLMProvider):
    """A local model served by Ollama over its HTTP API."""

    def __init__(self, settings: Settings) -> None:
        self._url = settings.ollama_base_url.rstrip("/") + "/api/generate"
        self._model = settings.ollama_model

    def generate(self, prompt: str, system: str | None = None) -> str:
        payload = {"model": self._model, "prompt": prompt, "stream": False}
        if system:
            payload["system"] = system
        resp = requests.post(self._url, json=payload, timeout=120)
        resp.raise_for_status()
        return resp.json().get("response", "").strip()


class MockProvider(LLMProvider):
    """Offline, deterministic provider for tests and keyless demos.

    It does not understand the question; it returns a predictable string so the
    pipeline can be exercised end-to-end without a real model. For invoice
    extraction (detected by the word 'JSON' in the prompt) it returns a valid,
    minimal JSON object so the Pydantic validation path is still exercised.
    """

    def generate(self, prompt: str, system: str | None = None) -> str:
        if "JSON" in (system or "") + prompt:
            return json.dumps({
                "invoice_number": None,
                "invoice_date": None,
                "currency": "USD",
                "shipper": {"name": "Unknown shipper", "address": None, "country": "India"},
                "consignee": {"name": "Unknown consignee", "address": None, "country": "Unknown"},
                "line_items": [],
                "declared_value": 0.0,
            })
        # RAG answer: echo a short deterministic sentence grounded in the prompt.
        return ("[mock LLM] This is a deterministic offline answer. Configure "
                "LLM_PROVIDER=gemini or ollama for real responses.")


def get_llm(settings: Settings | None = None) -> LLMProvider:
    """Factory: build the provider named by LLM_PROVIDER."""
    settings = settings or get_settings()
    provider = settings.llm_provider.lower()
    if provider == "gemini":
        return GeminiProvider(settings)
    if provider == "ollama":
        return OllamaProvider(settings)
    if provider == "mock":
        return MockProvider()
    raise ValueError(f"Unknown LLM_PROVIDER '{settings.llm_provider}'.")
