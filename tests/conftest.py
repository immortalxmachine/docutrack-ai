"""
Shared test configuration.

Force the offline 'mock' LLM provider and an isolated SQLite database BEFORE
any app module reads settings, so no test ever calls a real model or touches a
developer's database.
"""
from __future__ import annotations

import os
import tempfile

# Must be set before app.config.get_settings() is first cached.
os.environ["LLM_PROVIDER"] = "mock"
_DB_FILE = os.path.join(tempfile.gettempdir(), "docutrack_test.db")
if os.path.exists(_DB_FILE):
    os.remove(_DB_FILE)
os.environ["DATABASE_URL"] = f"sqlite:///{_DB_FILE}"
# Point retrieval at an empty dir so /ask is deterministically 503 (no index),
# and RAG logic is covered separately in test_rag.py with an injected store.
os.environ["INDEX_DIR"] = os.path.join(tempfile.gettempdir(), "docutrack_test_index_absent")
