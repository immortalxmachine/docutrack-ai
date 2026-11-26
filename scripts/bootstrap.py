"""
Idempotent first-run bootstrap: make sure sample data and the FAISS index exist.

Used by the Docker entrypoint so `docker compose up` yields a working system,
and handy locally too. Each step is skipped if its output already exists.
"""
from __future__ import annotations

import glob
import os

from app.config import get_settings
from app.vectorstore import VectorStore


def main() -> None:
    settings = get_settings()

    if not glob.glob(os.path.join(settings.docs_dir, "*.pdf")):
        from scripts.fetch_docs import main as fetch_docs
        fetch_docs()
    else:
        print(f"[bootstrap] docs already present in {settings.docs_dir}/")

    if not glob.glob(os.path.join("data", "invoices", "*.pdf")):
        from scripts.generate_invoices import main as gen_inv
        gen_inv()
    else:
        print("[bootstrap] invoices already present")

    if not VectorStore.exists(settings.index_dir):
        from app.ingest import build_index
        build_index()
    else:
        print(f"[bootstrap] FAISS index already present in {settings.index_dir}/")


if __name__ == "__main__":
    main()
