"""Embedding service with ModelScope BGE + offline fallback for Chinese text.

Architecture:
- BGE-small-zh-v1.5 via ModelScope (primary) — 512-dim semantic embeddings
- BGE-small-zh-v1.5 via HuggingFace (fallback)
- paraphrase-multilingual-MiniLM via HuggingFace (fallback)
- SimpleChineseEmbedding (last resort) — character n-gram hash, works offline
"""

import logging
import os
from pathlib import Path
from typing import List

import numpy as np

logger = logging.getLogger(__name__)

MODELSCOPE_CACHE = Path.home() / ".cache" / "modelscope" / "hub" / "models"
BGE_MODEL_NAME = "BAAI/bge-small-zh-v1.5"

_BGE_LOCAL_DIR: str | None = None


def _find_bge_local() -> str | None:
    global _BGE_LOCAL_DIR
    if _BGE_LOCAL_DIR:
        return _BGE_LOCAL_DIR
    if not MODELSCOPE_CACHE.exists():
        return None
    # ModelScope cache is two levels deep: org/model_name/
    for org_dir in MODELSCOPE_CACHE.iterdir():
        if not org_dir.is_dir():
            continue
        for model_dir in org_dir.iterdir():
            if model_dir.is_dir() and "bge-small-zh" in model_dir.name:
                config = model_dir / "config.json"
                if config.exists():
                    _BGE_LOCAL_DIR = str(model_dir)
                    return _BGE_LOCAL_DIR
    return None


def _modelscope_reachable() -> bool:
    import socket
    try:
        sock = socket.create_connection(("modelscope.cn", 443), timeout=2)
        sock.close()
        return True
    except OSError:
        return False


class EmbeddingFunction:
    """Protocol-compatible embedding function for ChromaDB."""

    def __call__(self, texts: List[str]) -> List[List[float]]:
        ...


class SimpleChineseEmbedding(EmbeddingFunction):
    """Character n-gram hash embedding for Chinese text.

    Deterministic, offline, requires no model downloads.
    Used as last-resort fallback only.
    """

    def __init__(self, dim: int = 384) -> None:
        self.dim = dim

    def __call__(self, texts: List[str]) -> List[List[float]]:
        results: List[List[float]] = []
        for text in texts:
            vec = np.zeros(self.dim, dtype=np.float64)
            for ch in text:
                vec[hash(ch) % self.dim] += 1
            for i in range(len(text) - 1):
                vec[hash(text[i : i + 2]) % self.dim] += 1
            for i in range(len(text) - 2):
                vec[hash(text[i : i + 3]) % self.dim] += 1
            norm = np.linalg.norm(vec)
            if norm > 0:
                vec = vec / norm
            results.append(vec.tolist())
        return results


class SentenceTransformerEmbedding(EmbeddingFunction):
    """Wrapper around SentenceTransformer for consistent __call__ interface."""

    def __init__(self, model) -> None:
        self._model = model

    def __call__(self, texts: List[str]) -> List[List[float]]:
        embeddings = self._model.encode(texts, normalize_embeddings=True)
        return embeddings.tolist()


def _load_bge_from_modelscope():
    """Load BGE model from ModelScope (local cache or download)."""
    local_dir = _find_bge_local()
    if local_dir:
        logger.info("Loading BGE from ModelScope cache: %s", local_dir)
        from sentence_transformers import SentenceTransformer
        return SentenceTransformer(local_dir)

    if not _modelscope_reachable():
        return None

    try:
        from modelscope import snapshot_download
        logger.info("Downloading BGE from ModelScope...")
        model_dir = snapshot_download(BGE_MODEL_NAME)
        from sentence_transformers import SentenceTransformer
        return SentenceTransformer(model_dir)
    except Exception:
        logger.warning("BGE download from ModelScope failed", exc_info=True)
        return None


def _load_bge_from_hf():
    """Load BGE from HuggingFace."""
    try:
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer(BGE_MODEL_NAME)
        _ = model.encode(["测试"])
        return model
    except Exception:
        logger.warning("BGE load from HuggingFace failed", exc_info=True)
        return None


def _load_minilm_from_hf():
    """Load multilingual MiniLM from HuggingFace."""
    try:
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")
        _ = model.encode(["test"])
        return model
    except Exception:
        logger.warning("MiniLM load from HuggingFace failed", exc_info=True)
        return None


def get_embedding_function() -> EmbeddingFunction:
    """Factory: returns the best available embedding function.

    Priority: ModelScope BGE > HuggingFace BGE > HuggingFace MiniLM > SimpleChinese
    """
    model = _load_bge_from_modelscope()
    if model is not None:
        return SentenceTransformerEmbedding(model)

    model = _load_bge_from_hf()
    if model is not None:
        return SentenceTransformerEmbedding(model)

    model = _load_minilm_from_hf()
    if model is not None:
        return SentenceTransformerEmbedding(model)

    logger.warning("No semantic model available, using SimpleChineseEmbedding")
    return SimpleChineseEmbedding()
