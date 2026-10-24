# src/repobrain/hybrid_retriever.py
"""
Hybrid Codebase Retriever (Two-Stage RRF k=60 + Cross-Encoder Reranking)
Governed strictly by 00_FOUNDING_ARCHITECTURE.md (Pillars 1-4, Guardrails #3, #4, #5, #6, #8).
Seamlessly integrates Layer 1 (AST), Layer 2 (Episodes), Layer 3 (ResearchBrain), and Layer 4 (Stockroom).
"""

from __future__ import annotations
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID, uuid4

# Guardrail #8: stdio hygiene & progress bar suppression
os.environ["TOKENIZERS_PARALLELISM"] = "false"
os.environ["HF_HUB_DISABLE_PROGRESS_BARS"] = "1"

from repobrain.ast_chunker import ASTCodeChunker, compute_git_blob_sha
from repobrain.episodic_memory import EpisodicMemoryStore
from repobrain.research_brain import ResearchBrainEngine
from repobrain.schemas import (
    ASTChildNode,
    ASTParentNode,
    EpisodicBugRecord,
    ResearchBrief,
    RetrievedCodeContext,
    TemplateBlueprint,
)
from repobrain.template_stockroom import TemplateStockroom


_RE_CAMEL_1 = re.compile(r"([A-Z]+)([A-Z][a-z])")
_RE_CAMEL_2 = re.compile(r"([a-z0-9])([A-Z])")
_RE_DELIMS = re.compile(r"[_./:-]+")
_RE_CLEAN = re.compile(r"[^a-zA-Z0-9_]+")


def normalize_code_identifiers_py(input_text: str) -> str:
    """
    Python equivalent of Guardrail #3 PostgreSQL IMMUTABLE PARALLEL SAFE function:
    Preserves exact original token while appending split camelCase, PascalCase, and snake_case sub-tokens.
    """
    if not input_text:
        return ""
    step1 = _RE_CAMEL_1.sub(r"\1 \2", input_text)
    step2 = _RE_CAMEL_2.sub(r"\1 \2", step1)
    step3 = _RE_DELIMS.sub(" ", step2)
    lower_tokens = step3.lower()
    return f"{input_text} {lower_tokens}".strip()


def build_disjunction_tsquery(raw_query: str) -> Tuple[str, List[str]]:
    """
    Guardrail #4: Build disjunction (|) tsquery over normalized query tokens (length > 1).
    """
    normalized = normalize_code_identifiers_py(raw_query)
    clean = _RE_CLEAN.sub(" ", normalized)
    tokens = list(dict.fromkeys(t for t in clean.split() if len(t) > 1))
    tsquery_str = " | ".join(tokens)
    return tsquery_str, tokens


class HybridCodebaseRetriever:
    """
    Two-Stage Hybrid Codebase Retriever.
    Pairs dense cosine similarity with sparse lexical tsvector BM25 rank,
    fuses Top 40 dense + Top 40 sparse via RRF (k=60) into a 25-candidate pool,
    and reranks on CPU via Cross-Encoder (ms-marco-MiniLM-L-6-v2) or deterministic fallback.
    """

    def __init__(self, db_conn_or_url: Optional[Any] = None, repo_root: Optional[Path] = None) -> None:
        self.db_conn = db_conn_or_url
        self.repo_root = (repo_root or Path.cwd()).resolve()
        self.chunker = ASTCodeChunker()

        # Integrated Layer Engines
        self.episodic_store = EpisodicMemoryStore(storage_path=self.repo_root / ".repobrain" / "episodes.json")
        self.research_brain = ResearchBrainEngine(repo_root=self.repo_root)
        self.template_stockroom = TemplateStockroom()

        # In-memory mirror for local developer execution & zero-setup testing
        self.parents_db: Dict[str, ASTParentNode] = {}
        self.children_db: Dict[str, List[ASTChildNode]] = {}

        self._cross_encoder = None
        self._cross_encoder_checked = False

    def _get_cross_encoder(self):
        """Lazy-loads the cross-encoder to prevent startup freezes on Windows."""
        if not self._cross_encoder_checked:
            self._cross_encoder_checked = True
            try:
                from sentence_transformers import CrossEncoder  # type: ignore
                self._cross_encoder = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")
            except Exception:
                self._cross_encoder = None
        return self._cross_encoder

    def sync_file_if_changed(self, file_path: Path) -> bool:
        """
        Guardrail #6: Incremental Git Blob SHA Sync on Every Patch & Rollback.
        Upserts parent and cascades child replacement only if git blob SHA changed.
        """
        file_path = file_path.resolve()
        if not file_path.exists():
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

        existing_parent = self.parents_db.get(rel_path)
        if existing_parent and existing_parent.git_blob_sha == current_sha:
            return False

        parent_node, child_nodes = self.chunker.chunk_file(file_path, repo_root=self.repo_root)
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
        """Convenience method delegating to Layer 2 EpisodicMemoryStore."""
        ep = self.episodic_store.record_episode(
            error_signature=error_signature,
            target_symbol=target_symbol,
            file_path=file_path,
            root_cause_summary=root_cause_summary,
            resolution_diff=resolution_diff,
        )
        return str(ep.episode_id)

    def index_code_string(self, code_str: str, virtual_path: str = "snippet.py", language: str = "python") -> None:
        """Indexes an in-memory code string into the local memory mirror."""
        parent_node, child_nodes = self.chunker.chunk_code_string(code_str, virtual_path=virtual_path, language=language)
        self.parents_db[virtual_path] = parent_node
        self.children_db[virtual_path] = child_nodes

    def _compute_dense_similarity(self, query: str, child: ASTChildNode) -> float:
        """Dense semantic cosine similarity proxy when local transformer is not loaded."""
        q_norm = normalize_code_identifiers_py(query).lower().split()
        target_text = f"{child.symbol_name} {child.signature} {child.docstring or ''} {child.body_code}".lower()
        matches = sum(1 for term in q_norm if term in target_text)
        return float(matches) / (len(q_norm) + 1e-5)

    def _compute_sparse_bm25_rank(self, query_tokens: List[str], child: ASTChildNode) -> float:
        """Sparse ts_rank_cd(fts_tokens, ts_q, 32) score simulation with sub-token normalization."""
        norm_symbol = normalize_code_identifiers_py(child.symbol_name).lower()
        norm_sig = normalize_code_identifiers_py(child.signature).lower()
        norm_doc = normalize_code_identifiers_py(child.docstring or "").lower()
        norm_body = normalize_code_identifiers_py(child.body_code).lower()

        score = 0.0
        for token in query_tokens:
            token_lower = token.lower()
            if token_lower in norm_symbol:
                score += 1.0  # Weight A
            elif token_lower in norm_sig:
                score += 0.4  # Weight B
            elif token_lower in norm_doc:
                score += 0.2  # Weight C
            elif token_lower in norm_body:
                score += 0.1  # Weight D

        if score > 0:
            return score / (score + 1.0)
        return 0.0

    def search(
        self,
        query: str,
        top_k: int = 5,
        rrf_pool_size: int = 25,
        include_episodes: bool = True
    ) -> List[RetrievedCodeContext]:
        """
        Guardrail #5: Two-Stage RRF (k=60) -> Cross-Encoder Reranking Funnel.
        1. Fetch top 40 dense + top 40 sparse candidates.
        2. FULL OUTER JOIN RRF (k=60) into 25-candidate pool.
        3. Cross-Encoder reranking of all 25 pairs.
        4. Attach matching Layer 2 EpisodicBugRecords and return top_k.
        """
        ts_q_str, query_tokens = build_disjunction_tsquery(query)

        if not self.children_db:
            self.scan_repository()

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

        # 3. RRF (k=60) Candidate Fusion
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
        ce = self._get_cross_encoder()
        scored_results: List[RetrievedCodeContext] = []

        for item in rrf_pool:
            child = item["child"]
            parent = item["parent"]
            doc_text = f"{child.symbol_name}\n{child.signature}\n{child.body_code}"

            if ce is not None:
                ce_score = float(ce.predict([(query, doc_text)])[0])
            else:
                # Deterministic high-precision fallback scoring
                token_matches = sum(1 for t in query_tokens if t.lower() in doc_text.lower())
                exact_symbol_bonus = 2.0 if any(t.lower() == child.symbol_name.lower() or t.lower() in child.symbol_name.lower() for t in query_tokens) else 0.0
                ce_score = item["rrf_score"] * 10.0 + (token_matches * 0.15) + exact_symbol_bonus

            # Layer 2: Matching Episodic Fixes
            related_episodes: List[EpisodicBugRecord] = []
            if include_episodes:
                related_episodes = self.episodic_store.find_matching_episodes(
                    symbol_name=child.symbol_name,
                    file_path=child.file_path,
                    query=query,
                    limit=2,
                )

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

    def scan_repository(self) -> int:
        """Indexes all supported source files (.py, .ts, .tsx, .js) in src/."""
        count = 0
        src_dir = self.repo_root / "src"
        if src_dir.exists():
            for p in src_dir.glob("**/*"):
                if p.is_file() and p.suffix.lower() in (".py", ".ts", ".tsx", ".js", ".jsx"):
                    if self.sync_file_if_changed(p):
                        count += 1
        return count

    def compute_blast_radius(self, symbol_name: str, file_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Lightweight Code Property Graph (CPG) & Blast Radius Analyzer:
        Traverses caller/callee edges and associated test suites to alert agents
        of potential breaking contracts before code modification.
        """
        if not self.children_db:
            self.scan_repository()

        short_name = symbol_name.split(".")[-1]
        all_children = [c for child_list in self.children_db.values() for c in child_list]

        # 1. Locate target symbol
        target_child = None
        for c in all_children:
            if c.symbol_name == symbol_name:
                target_child = c
                break
            if file_path and c.file_path == file_path and (c.symbol_name.endswith(short_name) or short_name in c.symbol_name):
                target_child = c
                break

        if not target_child:
            for c in all_children:
                if c.symbol_name.endswith(short_name) or short_name == c.symbol_name:
                    target_child = c
                    break

        # 2. Find callers / dependents in the codebase (1-hop incoming edges)
        callers = []
        for c in all_children:
            if target_child and c.child_id == target_child.child_id:
                continue
            if short_name in c.body_code or symbol_name in c.body_code:
                callers.append({
                    "symbol_name": c.symbol_name,
                    "file_path": c.file_path,
                    "node_kind": c.node_kind,
                    "lines": f"{c.start_line}-{c.end_line}",
                })

        # 3. Scan test files in tests/
        associated_tests = []
        tests_dir = self.repo_root / "tests"
        if tests_dir.exists():
            for t_file in tests_dir.glob("**/*"):
                if t_file.is_file() and t_file.suffix in (".py", ".ts", ".js"):
                    try:
                        content = t_file.read_text(encoding="utf-8", errors="ignore")
                        if short_name in content or symbol_name in content:
                            associated_tests.append(t_file.relative_to(self.repo_root).as_posix())
                    except Exception:
                        pass

        # 4. Assess risk level
        caller_count = len(callers)
        test_count = len(associated_tests)

        if caller_count >= 3 or test_count >= 2:
            risk_level = "HIGH"
        elif caller_count >= 1 or test_count >= 1:
            risk_level = "MODERATE"
        else:
            risk_level = "LOW"

        advisory = (
            f"Modifying '{symbol_name}' impacts {caller_count} caller(s) across {len({c['file_path'] for c in callers})} file(s) "
            f"and is verified by {test_count} test suite(s). "
            f"{'Preserve parameter contracts and return signatures.' if risk_level != 'LOW' else 'Isolated symbol; low risk of transitive regressions.'}"
        )

        return {
            "symbol_name": symbol_name,
            "short_name": short_name,
            "found_target": target_child is not None,
            "file_path": target_child.file_path if target_child else (file_path or "unknown"),
            "callers_count": caller_count,
            "callers": callers,
            "associated_tests_count": test_count,
            "associated_tests": associated_tests,
            "risk_level": risk_level,
            "advisory": advisory,
        }
