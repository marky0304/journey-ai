"""Pure Python vector store for knowledge indexing and retrieval.

Uses numpy for cosine similarity — no C extensions needed.
Fast enough for <50K documents with 512-dim vectors.

Features:
- Text chunking: splits long docs into 512-char overlapping chunks
- BM25 hybrid retrieval: vector similarity + keyword scoring
- JSON-file persistence via a simple document store
"""

import json
import logging
import os
from math import log
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np

from app.services.embedding_service import EmbeddingFunction, get_embedding_function

logger = logging.getLogger(__name__)

CHUNK_SIZE = 512
CHUNK_OVERLAP = 128


def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> List[str]:
    """Split long text into overlapping chunks, preferring sentence boundaries."""
    if len(text) <= chunk_size:
        return [text]

    chunks: List[str] = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]

        if end < len(text):
            for sep in ("。", "！", "？", "\n\n", "\n", "；", "，", " "):
                pos = chunk.rfind(sep, start + chunk_size // 2)
                if pos != -1:
                    end = pos + 1
                    chunk = text[start:end]
                    break

        chunks.append(chunk.strip())
        start = end - overlap
        if start >= len(text):
            break

    return chunks


class BM25Scorer:
    """Lightweight BM25 scorer for Chinese/English hybrid retrieval."""

    def __init__(self, k1: float = 1.2, b: float = 0.75) -> None:
        self.k1 = k1
        self.b = b
        self._docs: List[List[str]] = []
        self._avgdl: float = 0
        self._df: Dict[str, int] = {}
        self._idf: Dict[str, float] = {}
        self._doc_count: int = 0

    def index(self, documents: List[str]) -> None:
        self._docs = [self._tokenize(d) for d in documents]
        self._doc_count = len(self._docs)
        if self._doc_count == 0:
            return
        self._avgdl = sum(len(d) for d in self._docs) / self._doc_count
        self._df = {}
        for doc in self._docs:
            seen: set = set()
            for token in doc:
                if token not in seen:
                    self._df[token] = self._df.get(token, 0) + 1
                    seen.add(token)
        self._idf = {}
        for token, df in self._df.items():
            self._idf[token] = log((self._doc_count - df + 0.5) / (df + 0.5) + 1.0)

    def score(self, query: str, doc_idx: int) -> float:
        if doc_idx >= len(self._docs):
            return 0.0
        query_tokens = self._tokenize(query)
        doc = self._docs[doc_idx]
        doc_len = len(doc)
        score = 0.0
        tf: Dict[str, int] = {}
        for t in doc:
            tf[t] = tf.get(t, 0) + 1
        for token in query_tokens:
            if token not in self._idf:
                continue
            f = tf.get(token, 0)
            if f == 0:
                continue
            numerator = f * (self.k1 + 1)
            denominator = f + self.k1 * (1 - self.b + self.b * doc_len / self._avgdl)
            score += self._idf[token] * numerator / denominator
        return score

    @staticmethod
    def _tokenize(text: str) -> List[str]:
        tokens: List[str] = []
        for i in range(len(text) - 1):
            if text[i] == " " or text[i + 1] == " ":
                continue
            tokens.append(text[i : i + 2])
        for ch in text:
            if ch.strip() and not ch.isascii():
                tokens.append(ch)
        return tokens


class VectorStoreService:
    """Numpy-backed vector store with JSON persistence and hybrid retrieval."""

    def __init__(self, persist_path: str = "./vector_data") -> None:
        self._persist_dir = Path(persist_path)
        self._persist_dir.mkdir(parents=True, exist_ok=True)
        self._fn: EmbeddingFunction = get_embedding_function()

        # In-memory storage
        self._ids: List[str] = []
        self._documents: List[str] = []
        self._metadatas: List[Dict] = []
        self._vectors: Optional[np.ndarray] = None  # shape: (n, dim)

        self._bm25: Optional[BM25Scorer] = None
        self._dim: int = 0

        self._load()

    # ── persistence ────────────────────────────────────────────

    def _data_path(self) -> Path:
        return self._persist_dir / "vectors.json"

    def _save(self) -> None:
        data = {
            "ids": self._ids,
            "documents": self._documents,
            "metadatas": self._metadatas,
            "vectors": self._vectors.tolist() if self._vectors is not None else [],
            "dim": self._dim,
        }
        tmp = self._data_path().with_suffix(".tmp")
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False)
        os.replace(tmp, self._data_path())

    def _load(self) -> None:
        path = self._data_path()
        if not path.exists():
            return
        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
            self._ids = data.get("ids", [])
            self._documents = data.get("documents", [])
            self._metadatas = data.get("metadatas", [])
            vectors = data.get("vectors", [])
            self._dim = data.get("dim", 0)
            if vectors:
                self._vectors = np.array(vectors, dtype=np.float32)
            self._rebuild_bm25()
            logger.info("Loaded %d documents from %s", len(self._ids), path)
        except Exception:
            logger.warning("Failed to load vector data, starting fresh")

    def _rebuild_bm25(self) -> None:
        if self._documents:
            self._bm25 = BM25Scorer()
            self._bm25.index(self._documents)

    # ── indexing ───────────────────────────────────────────────

    def index_knowledge(
        self,
        knowledge_id: str,
        text: str,
        metadata: Optional[Dict] = None,
    ) -> int:
        """Index a document with chunking. Returns number of chunks."""
        meta = metadata or {}
        chunks = chunk_text(text)

        # Delete existing entries for this document
        self._delete_by_parent(knowledge_id)

        embeddings = self._fn(chunks)
        vecs = np.array(embeddings, dtype=np.float32)

        if len(chunks) == 1:
            ids = [knowledge_id]
            metas = [meta]
        else:
            ids = [f"{knowledge_id}_chunk{i}" for i in range(len(chunks))]
            metas = [
                {**meta, "chunk_index": i, "parent_id": knowledge_id}
                for i in range(len(chunks))
            ]

        self._ids.extend(ids)
        self._documents.extend(chunks)
        self._metadatas.extend(metas)

        if self._vectors is None:
            self._vectors = vecs
            self._dim = vecs.shape[1]
        else:
            self._vectors = np.vstack([self._vectors, vecs])

        self._rebuild_bm25()
        self._save()
        logger.info("Indexed %d chunks for doc %s", len(chunks), knowledge_id)
        return len(chunks)

    def _delete_by_parent(self, parent_id: str) -> None:
        """Remove all chunks belonging to a parent document."""
        indices = [
            i for i, m in enumerate(self._metadatas)
            if m.get("parent_id") == parent_id or self._ids[i] == parent_id
        ]
        if not indices:
            return
        keep = [i for i in range(len(self._ids)) if i not in indices]
        self._ids = [self._ids[i] for i in keep]
        self._documents = [self._documents[i] for i in keep]
        self._metadatas = [self._metadatas[i] for i in keep]
        if self._vectors is not None and len(keep) > 0:
            self._vectors = self._vectors[keep]
        elif len(keep) == 0:
            self._vectors = None

    # ── search ─────────────────────────────────────────────────

    def search(
        self,
        query: str,
        n_results: int = 5,
        where: Optional[Dict] = None,
        hybrid_weight: float = 0.7,
    ) -> List[Dict]:
        """Hybrid search: vector similarity + BM25 keyword scoring."""
        if self._vectors is None or len(self._ids) == 0:
            return []

        # Filter by metadata
        indices = list(range(len(self._ids)))
        if where:
            indices = [
                i for i in indices
                if all(
                    self._metadatas[i].get(k) == v
                    for k, v in where.items()
                )
            ]
        if not indices:
            return []

        # Vector similarity
        query_vec = np.array(self._fn([query]), dtype=np.float32)
        sub_vectors = self._vectors[indices]
        # Cosine similarity
        norms = np.linalg.norm(sub_vectors, axis=1)
        q_norm = np.linalg.norm(query_vec)
        denom = norms * q_norm
        denom[denom == 0] = 1e-10
        sims = np.dot(sub_vectors, query_vec.T).flatten() / denom
        distances = 1.0 - sims  # convert to distance

        # Get top candidates
        k = min(max(n_results * 3, 20), len(indices))
        top_k = np.argsort(distances)[:k]

        items: List[Dict] = []
        for idx in top_k:
            global_idx = indices[idx]
            items.append({
                "id": self._ids[global_idx],
                "document": self._documents[global_idx],
                "metadata": self._metadatas[global_idx],
                "distance": float(distances[idx]),
            })

        # Hybrid rerank
        if self._bm25 and hybrid_weight < 1.0:
            items = self._hybrid_rerank(query, items, hybrid_weight)

        return self._deduplicate(items, n_results)

    def _hybrid_rerank(
        self, query: str, items: List[Dict], hybrid_weight: float
    ) -> List[Dict]:
        distances = [d["distance"] for d in items]
        min_d, max_d = min(distances), max(distances)
        if max_d - min_d < 0.001:
            vec_scores = [0.5 for _ in distances]
        else:
            vec_scores = [1.0 - (d - min_d) / (max_d - min_d) for d in distances]

        for idx, item in enumerate(items):
            bm25_score = 0.0
            for bm_idx, bm_doc in enumerate(self._documents):
                if bm_doc == item["document"] or self._ids[bm_idx] == item["id"]:
                    bm25_score = max(bm25_score, self._bm25.score(query, bm_idx))
            bm25_norm = 1.0 / (1.0 + np.exp(-bm25_score / 4))
            item["hybrid_score"] = hybrid_weight * vec_scores[idx] + (1 - hybrid_weight) * bm25_norm
            item["vector_score"] = round(vec_scores[idx], 4)
            item["bm25_score"] = round(bm25_norm, 4)

        return items

    def _deduplicate(self, items: List[Dict], n_results: int) -> List[Dict]:
        """Keep only the best chunk per parent document."""
        seen: set = set()
        deduped: List[Dict] = []
        key = lambda x: x.get("hybrid_score", 1 - x["distance"])
        for item in sorted(items, key=key, reverse=True):
            parent = item["metadata"].get("parent_id", item["id"])
            if parent in seen:
                continue
            seen.add(parent)
            deduped.append(item)
            if len(deduped) >= n_results:
                break
        return deduped

    # ── management ─────────────────────────────────────────────

    def delete(self, knowledge_id: str) -> None:
        self._delete_by_parent(knowledge_id)
        self._rebuild_bm25()
        self._save()

    def count(self) -> int:
        return len(self._ids)


_vector_store: Optional[VectorStoreService] = None


def get_vector_store() -> VectorStoreService:
    global _vector_store
    if _vector_store is None:
        _vector_store = VectorStoreService()
    return _vector_store
