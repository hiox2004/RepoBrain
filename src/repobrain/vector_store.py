# src/repobrain/vector_store.py
"""
RepoBrain Embedded Persistent Vector Cache
Provides zero-setup, sub-millisecond cosine vector similarity
persisted to .repobrain/vector_cache.json without requiring external servers.
"""

from __future__ import annotations
import json
import logging
import math
import os
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

from repobrain.hybrid_retriever import normalize_code_identifiers_py
from repobrain.schemas import ASTChildNode

logger = logging.getLogger("RepoBrain.VectorStore")


class EmbeddedVectorIndex:
    """
    In-process, zero-dependency persistent vector index.
    Generates normalized sub-token frequency vectors and computes cosine similarity
    for candidate generation with sub-millisecond retrieval speeds.
    """

    def __init__(self, cache_file_path: Optional[Path] = None) -> None:
        self.cache_file = cache_file_path or (Path.cwd() / ".repobrain" / "vector_cache.json")
        # child_id -> { "symbol_name": ..., "file_path": ..., "git_blob_sha": ..., "vector": {token: weight}, "norm": float }
        self._entries: Dict[str, Dict[str, Any]] = {}
        self._dirty = False
        self.load()

    def _tokenize_text(self, text: str) -> List[str]:
        """Normalizes and splits text into sub-tokens."""
        norm = normalize_code_identifiers_py(text)
        return [t.lower() for t in norm.split() if len(t) > 1]

    def _compute_vector(self, tokens: List[str]) -> Tuple[Dict[str, float], float]:
        """Builds a term frequency vector and computes its L2 Euclidean norm."""
        counts = Counter(tokens)
        vec: Dict[str, float] = {}
        sum_sq = 0.0

        for tok, count in counts.items():
            # Sub-linear term frequency scaling: 1 + ln(count)
            weight = 1.0 + math.log(count)
            vec[tok] = weight
            sum_sq += weight * weight

        norm = math.sqrt(sum_sq) if sum_sq > 0 else 1.0
        return vec, norm

    def index_child(self, child: ASTChildNode, git_blob_sha: str) -> None:
        """Indexes an ASTChildNode into the vector store."""
        cid = str(child.child_id)
        # Weighted composite document text
        symbol_text = f"{child.symbol_name} {child.symbol_name} {child.symbol_name}"  # 3x weight
        sig_text = f"{child.signature} {child.signature}"  # 2x weight
        doc_text = child.docstring or ""
        body_text = child.body_code[:1500]  # First 1.5k chars

        full_text = f"{symbol_text} {sig_text} {doc_text} {body_text}"
        tokens = self._tokenize_text(full_text)
        vec, norm = self._compute_vector(tokens)

        self._entries[cid] = {
            "symbol_name": child.symbol_name,
            "file_path": child.file_path,
            "git_blob_sha": git_blob_sha,
            "vector": vec,
            "norm": norm,
        }
        self._dirty = True

    def remove_file(self, file_path: str) -> int:
        """Removes all indexed child entries associated with a file path."""
        to_del = [cid for cid, item in self._entries.items() if item["file_path"] == file_path]
        for cid in to_del:
            del self._entries[cid]
        if to_del:
            self._dirty = True
        return len(to_del)

    def search_top_k(self, query: str, top_k: int = 40) -> List[Tuple[str, float]]:
        """
        Executes sub-millisecond cosine vector similarity search.
        Returns sorted list of (child_id, cosine_score) pairs.
        """
        q_tokens = self._tokenize_text(query)
        if not q_tokens:
            return []

        q_vec, q_norm = self._compute_vector(q_tokens)
        scores: List[Tuple[str, float]] = []

        for cid, entry in self._entries.items():
            target_vec = entry["vector"]
            target_norm = entry["norm"]

            # Sparse dot product over intersecting tokens
            dot = 0.0
            for tok, q_w in q_vec.items():
                if tok in target_vec:
                    dot += q_w * target_vec[tok]

            if dot > 0:
                cosine = dot / (q_norm * target_norm)
                scores.append((cid, cosine))

        scores.sort(key=lambda x: x[1], reverse=True)
        return scores[:top_k]

    def save(self) -> bool:
        """Flushes the vector index to disk if dirty."""
        if not self._dirty:
            return False
        try:
            self.cache_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.cache_file, "w", encoding="utf-8") as f:
                json.dump(self._entries, f, indent=2)
            self._dirty = False
            return True
        except Exception as e:
            logger.error("Failed to save vector cache: %s", e)
            return False

    def load(self) -> bool:
        """Loads the vector index from disk."""
        if not self.cache_file.exists():
            return False
        try:
            with open(self.cache_file, "r", encoding="utf-8") as f:
                self._entries = json.load(f)
            self._dirty = False
            return True
        except Exception as e:
            logger.warning("Failed to load vector cache: %s", e)
            return False

    def size(self) -> int:
        return len(self._entries)
