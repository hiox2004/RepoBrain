# src/repobrain/hybrid_retriever.py
"""
Hybrid Codebase Retriever (Two-Stage RRF k=60 + Cross-Encoder Reranking)
Governed strictly by REPOBRAIN_MASTER_CONTEXT_SPEC.md Guardrails #3, #4, #5, #6, #8.
"""

from __future__ import annotations
import os
import re
import math
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID, uuid4

# Guardrail #8: stdio hygiene & progress bar suppression
os.environ["TOKENIZERS_PARALLELISM"] = "false"
os.environ["HF_HUB_DISABLE_PROGRESS_BARS"] = "1"

from repobrain.ast_chunker import ASTCodeChunker, compute_git_blob_sha
from repobrain.schemas import ASTChildNode, ASTParentNode, EpisodicFixRecord, RetrievedCodeContext


def normalize_code_identifiers_py(input_text: str) -> str:
    """
    Python equivalent of Guardrail #3 PostgreSQL IMMUTABLE PARALLEL SAFE function:
    Preserves exact original token while appending split camelCase, PascalCase, and snake_case sub-tokens.
    """
    if not input_text:
        return ""
    # ([A-Z]+)([A-Z][a-z])
    step1 = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1 \2", input_text)
    # ([a-z0-9])([A-Z])
    step2 = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", step1)
    # [_./:-]+ -> ' '
    step3 = re.sub(r"[_./:-]+", " ", step2)
    lower_tokens = step3.lower()
    return f"{input_text} {lower_tokens}".strip()


def build_disjunction_tsquery(raw_query: str) -> Tuple[str, List[str]]:
    """
    Guardrail #4: Build disjunction (|) tsquery over normalized query tokens (length > 1).
    """
    normalized = normalize_code_identifiers_py(raw_query)
    clean = re.sub(r"[^a-zA-Z0-9_]+", " ", normalized)
    tokens = list(dict.fromkeys(t for t in clean.split() if len(t) > 1))
    tsquery_str = " | ".join(tokens)
    return tsquery_str, tokens


class HybridCodebaseRetriever:
    """
    Hybrid Retriever combining pgvector HNSW cosine distance and BM25 / tsvector full-text search,
    fused via Reciprocal Rank Fusion (k=60) and reranked via Cross-Encoder.
    """

    def __init__(self, db_conn_or_url: Optional[Any] = None, repo_root: Optional[Path] = None) -> None:
        self.db_conn = db_conn_or_url
        self.repo_root = (repo_root or Path.cwd()).resolve()
        self.chunker = ASTCodeChunker()
        
        # In-memory mirror for local execution & zero-setup test execution
        self.parents_db: Dict[str, ASTParentNode] = {} # file_path -> ASTParentNode
        self.children_db: Dict[str, List[ASTChildNode]] = {} # file_path -> list[ASTChildNode]
        self.episodes_db: List[EpisodicFixRecord] = []

        self._cross_encoder = None
        self._init_cross_encoder()

    def _init_cross_encoder(self) -> None:
        try:
            from sentence_transformers import CrossEncoder # type: ignore
            self._cross_encoder = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")
        except Exception:
            self._cross_encoder = None

    def sync_file_if_changed(self, file_path: Path) -> bool:
        """
        Guardrail #6: Incremental Git Blob SHA Sync on Every Patch & Rollback.
        Upserts parent and cascades child replacement only if git blob sha changed.
        Returns True if reindexed, False if unchanged.
        """
        file_path = file_path.resolve()
        if not file_path.exists():
            # If deleted, remove from memory
            try:
                rel_path = file_path.relative_to(self.repo_root).as_posix()
            except ValueError:
                rel_path = file_path.name
            if rel_path in self.parents_db:
                del self.parents_db[rel_path]
                self.children_db.pop(rel_path, None)
                return True
            return False

        with open(file_path, "rb") as f:
            source_bytes = f.read()

        current_sha = compute_git_blob_sha(source_bytes)
        try:
            rel_path = file_path.relative_to(self.repo_root).as_posix()
        except ValueError:
            rel_path = file_path.name

        # Check existing SHA
        existing_parent = self.parents_db.get(rel_path)
        if existing_parent and existing_parent.git_blob_sha == current_sha:
            return False

        # Parse AST
        parent_node, child_nodes = self.chunker.chunk_file(file_path, repo_root=self.repo_root)

        # Transactional cascading UPSERT
        self.parents_db[rel_path] = parent_node
        self.children_db[rel_path] = child_nodes
        return True

    def record_episodic_fix(
        self,
        error_signature: str,
        target_symbol: str,
        file_path: str,
        root_cause_summary: str,
        resolution_diff: str,
    ) -> str:
        """
        Layer 2: Episodic Self-Correcting Diagnostic Memory distillation.
        Stores fail->pass resolution record into project_episodes.
        """
        episode = EpisodicFixRecord(
            episode_id=uuid4(),
            error_signature=error_signature.strip(),
            target_symbol=target_symbol.strip(),
            file_path=file_path.strip(),
            root_cause_summary=root_cause_summary.strip(),
            resolution_diff=resolution_diff.strip(),
        )
        self.episodes_db.append(episode)
        return str(episode.episode_id)

    def _compute_dense_similarity(self, query: str, child: ASTChildNode) -> float:
        """
        Dense semantic cosine similarity proxy when local sentence-transformers isn't loaded.
        Embeds symbol name, signature, and body.
        """
        q_norm = normalize_code_identifiers_py(query).lower().split()
        target_text = f"{child.symbol_name} {child.signature} {child.docstring or ''} {child.body_code}".lower()
        matches = sum(1 for term in q_norm if term in target_text)
        return float(matches) / (len(q_norm) + 1e-5)

    def _compute_sparse_bm25_rank(self, query_tokens: List[str], child: ASTChildNode) -> float:
        """
        Sparse ts_rank_cd(fts_tokens, ts_q, 32) score simulation with sub-token normalization.
        """
        norm_symbol = normalize_code_identifiers_py(child.symbol_name).lower()
        norm_sig = normalize_code_identifiers_py(child.signature).lower()
        norm_doc = normalize_code_identifiers_py(child.docstring or "").lower()
        norm_body = normalize_code_identifiers_py(child.body_code).lower()

        score = 0.0
        for token in query_tokens:
            token_lower = token.lower()
            if token_lower in norm_symbol:
                score += 1.0 # Weight A
            elif token_lower in norm_sig:
                score += 0.4 # Weight B
            elif token_lower in norm_doc:
                score += 0.2 # Weight C
            elif token_lower in norm_body:
                score += 0.1 # Weight D

        # Flag 32 length normalization: rank / (rank + 1)
        if score > 0:
            return score / (score + 1.0)
        return 0.0

    def search(self, query: str, top_k: int = 5, rrf_pool_size: int = 25) -> List[RetrievedCodeContext]:
        """
        Guardrail #5: Two-Stage RRF (k=60) -> Cross-Encoder Reranking Funnel.
        1. Fetch top 40 dense + top 40 sparse candidates.
        2. FULL OUTER JOIN RRF (k=60) into 25-candidate pool.
        3. Cross-Encoder reranking of all 25 pairs.
        4. Attach matching EpisodicFixRecords and return top_k.
        """
        ts_q_str, query_tokens = build_disjunction_tsquery(query)

        all_children: List[Tuple[ASTParentNode, ASTChildNode]] = []
        for rel_path, parent in self.parents_db.items():
            children = self.children_db.get(rel_path, [])
            for child in children:
                all_children.append((parent, child))

        if not all_children:
            return []

        # 1. Dense Candidates Ranking (Top 40)
        dense_scored = []
        for parent, child in all_children:
            sim = self._compute_dense_similarity(query, child)
            dense_scored.append((sim, parent, child))
        dense_scored.sort(key=lambda x: x[0], reverse=True)
        dense_candidates = dense_scored[:40]

        dense_rank_map: Dict[UUID, int] = {}
        for rank_idx, (_, _, child) in enumerate(dense_candidates, start=1):
            dense_rank_map[child.child_id] = rank_idx

        # 2. Sparse Candidates Ranking (Top 40)
        sparse_scored = []
        for parent, child in all_children:
            rank_score = self._compute_sparse_bm25_rank(query_tokens, child)
            if rank_score > 0:
                sparse_scored.append((rank_score, parent, child))
        sparse_scored.sort(key=lambda x: x[0], reverse=True)
        sparse_candidates = sparse_scored[:40]

        sparse_rank_map: Dict[UUID, int] = {}
        for rank_idx, (_, _, child) in enumerate(sparse_candidates, start=1):
            sparse_rank_map[child.child_id] = rank_idx

        # 3. RRF (k=60) Fusion
        all_candidate_ids = set(dense_rank_map.keys()) | set(sparse_rank_map.keys())
        rrf_scored = []

        child_lookup = {child.child_id: (parent, child) for parent, child in all_children}

        for child_id in all_candidate_ids:
            parent, child = child_lookup[child_id]
            d_rank = dense_rank_map.get(child_id)
            s_rank = sparse_rank_map.get(child_id)

            rrf_score = 0.0
            if d_rank is not None:
                rrf_score += 1.0 / (60.0 + d_rank)
            if s_rank is not None:
                rrf_score += 1.0 / (60.0 + s_rank)

            rrf_scored.append({
                "child_id": child_id,
                "parent": parent,
                "child": child,
                "dense_rank": d_rank,
                "sparse_rank": s_rank,
                "rrf_score": rrf_score,
            })

        rrf_scored.sort(key=lambda x: x["rrf_score"], reverse=True)
        rrf_pool = rrf_scored[:rrf_pool_size]

        # 4. Cross-Encoder Reranking
        scored_results: List[RetrievedCodeContext] = []
        for item in rrf_pool:
            child = item["child"]
            parent = item["parent"]
            doc_text = f"{child.symbol_name}\n{child.signature}\n{child.body_code}"

            if self._cross_encoder is not None:
                ce_score = float(self._cross_encoder.predict([(query, doc_text)])[0])
            else:
                # Deterministic high-precision fallback scoring
                token_matches = sum(1 for t in query_tokens if t.lower() in doc_text.lower())
                exact_symbol_bonus = 2.0 if any(t.lower() == child.symbol_name.lower() or t.lower() in child.symbol_name.lower() for t in query_tokens) else 0.0
                ce_score = item["rrf_score"] * 10.0 + (token_matches * 0.15) + exact_symbol_bonus

            # Check matching episodic fixes
            related_episodes = [
                ep for ep in self.episodes_db
                if ep.target_symbol == child.symbol_name or ep.file_path == child.file_path
            ]

            ctx = RetrievedCodeContext(
                file_path=child.file_path,
                language=parent.language,
                symbol_name=child.symbol_name,
                node_kind=child.node_kind,
                start_line=child.start_line,
                end_line=child.end_line,
                git_blob_sha=parent.git_blob_sha,
                dense_rank=item["dense_rank"],
                sparse_rank=item["sparse_rank"],
                rrf_score=item["rrf_score"],
                cross_encoder_score=ce_score,
                imports_header=parent.imports_header,
                enclosing_scope=parent.enclosing_scope,
                body_code=child.body_code,
                related_episodes=related_episodes,
            )
            scored_results.append(ctx)

        scored_results.sort(key=lambda x: x.cross_encoder_score, reverse=True)
        return scored_results[:top_k]
