"""
A thin FAISS wrapper.

Stores two things side by side:
  * a FAISS IndexFlatIP (exact inner-product search over normalised vectors)
  * a parallel list of chunk metadata ({file, page, text}) in the same order

IndexFlatIP is brute-force (exact) search. With only a few thousand chunks that
is instant and avoids the tuning a quantised index needs — a deliberate
"simple and correct" choice for this corpus size.
"""
from __future__ import annotations

import json
import os

import faiss
import numpy as np


class VectorStore:
    def __init__(self, dim: int) -> None:
        self.dim = dim
        self.index = faiss.IndexFlatIP(dim)   # inner product == cosine (vectors are normalised)
        self.metadata: list[dict] = []

    # -- build --------------------------------------------------------------
    def add(self, vectors: np.ndarray, metadatas: list[dict]) -> None:
        if len(vectors) != len(metadatas):
            raise ValueError("vectors and metadatas must be the same length")
        self.index.add(vectors)
        self.metadata.extend(metadatas)

    # -- query --------------------------------------------------------------
    def search(self, query_vector: np.ndarray, k: int) -> list[tuple[dict, float]]:
        """Return up to k (metadata, similarity) pairs, best first."""
        if self.index.ntotal == 0:
            return []
        k = min(k, self.index.ntotal)
        scores, idxs = self.index.search(query_vector, k)
        results: list[tuple[dict, float]] = []
        for score, idx in zip(scores[0], idxs[0], strict=False):
            if idx == -1:
                continue
            results.append((self.metadata[idx], float(score)))
        return results

    # -- persistence --------------------------------------------------------
    @property
    def size(self) -> int:
        return self.index.ntotal

    def save(self, directory: str) -> None:
        os.makedirs(directory, exist_ok=True)
        faiss.write_index(self.index, os.path.join(directory, "index.faiss"))
        with open(os.path.join(directory, "meta.json"), "w", encoding="utf-8") as fh:
            json.dump({"dim": self.dim, "metadata": self.metadata}, fh, ensure_ascii=False)

    @classmethod
    def load(cls, directory: str) -> "VectorStore":
        index_path = os.path.join(directory, "index.faiss")
        meta_path = os.path.join(directory, "meta.json")
        if not (os.path.exists(index_path) and os.path.exists(meta_path)):
            raise FileNotFoundError(
                f"No index found in '{directory}'. Run: python -m app.ingest"
            )
        with open(meta_path, encoding="utf-8") as fh:
            meta = json.load(fh)
        store = cls(dim=meta["dim"])
        store.index = faiss.read_index(index_path)
        store.metadata = meta["metadata"]
        return store

    @staticmethod
    def exists(directory: str) -> bool:
        return os.path.exists(os.path.join(directory, "index.faiss"))
