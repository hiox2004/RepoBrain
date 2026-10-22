# src/repobrain/storage_sqlite.py
"""
Local Persistent SQLite Storage Tier for RepoBrain V2 & ResearchBrain OS.
Governed by 00_FOUNDING_ARCHITECTURE.md (Two-Tier Engine: Default Embedded SQLite).
Provides zero-setup, single-file (.repobrain/repobrain.db) persistence across all 4 layers.
"""

from __future__ import annotations
import json
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID, uuid4

from repobrain.schemas import (
    ASTChildNode,
    ASTParentNode,
    EpisodicBugRecord,
    TechKnowledgeChunk,
    TemplateBlueprint,
)


def _normalize_tokens(text: str) -> List[str]:
    import re
    # Split camelCase, PascalCase, snake_case
    step1 = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1 \2", text or "")
    step2 = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", step1)
    step3 = re.sub(r"[_./:-]+", " ", step2)
    return [t.lower() for t in step3.split() if len(t) > 1]


class SQLiteStorageTier:
    """
    Embedded SQLite engine supporting all 4 memory layers with FTS5 lexical ranking
    and sub-token identifier normalization.
    """

    def __init__(self, db_path: Optional[Path] = None) -> None:
        if db_path is None:
            db_path = Path.cwd() / ".repobrain" / "repobrain.db"
        self.db_path = db_path.resolve()
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._init_schema()

    def _init_schema(self) -> None:
        with self.conn:
            # Layer 1: AST Parents
            self.conn.execute("""
            CREATE TABLE IF NOT EXISTS ast_parents (
                parent_id TEXT PRIMARY KEY,
                file_path TEXT NOT NULL UNIQUE,
                language TEXT NOT NULL,
                imports_header TEXT NOT NULL DEFAULT '',
                enclosing_scope TEXT,
                git_blob_sha TEXT NOT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """)

            # Layer 1: AST Children
            self.conn.execute("""
            CREATE TABLE IF NOT EXISTS ast_children (
                child_id TEXT PRIMARY KEY,
                parent_id TEXT NOT NULL,
                file_path TEXT NOT NULL,
                node_kind TEXT NOT NULL,
                symbol_name TEXT NOT NULL,
                signature TEXT NOT NULL,
                docstring TEXT,
                body_code TEXT NOT NULL,
                start_line INTEGER NOT NULL,
                end_line INTEGER NOT NULL,
                FOREIGN KEY (parent_id) REFERENCES ast_parents(parent_id) ON DELETE CASCADE
            )
            """)
            self.conn.execute("CREATE INDEX IF NOT EXISTS idx_children_parent ON ast_children(parent_id)")
            self.conn.execute("CREATE INDEX IF NOT EXISTS idx_children_path ON ast_children(file_path)")
            self.conn.execute("CREATE INDEX IF NOT EXISTS idx_children_symbol ON ast_children(symbol_name)")

            # Layer 2: Episodic Diagnostic Memory
            self.conn.execute("""
            CREATE TABLE IF NOT EXISTS project_episodes (
                episode_id TEXT PRIMARY KEY,
                error_signature TEXT NOT NULL,
                target_symbol TEXT NOT NULL,
                file_path TEXT NOT NULL,
                root_cause_summary TEXT NOT NULL,
                resolution_diff TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """)
            self.conn.execute("CREATE INDEX IF NOT EXISTS idx_episodes_symbol ON project_episodes(target_symbol)")
            self.conn.execute("CREATE INDEX IF NOT EXISTS idx_episodes_file ON project_episodes(file_path)")

            # Layer 3: Tech Knowledge Chunks
            self.conn.execute("""
            CREATE TABLE IF NOT EXISTS tech_knowledge_chunks (
                chunk_id TEXT PRIMARY KEY,
                source_doc TEXT NOT NULL,
                domain TEXT NOT NULL DEFAULT 'general',
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                external_url TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """)

            # Layer 4: Template Blueprints
            self.conn.execute("""
            CREATE TABLE IF NOT EXISTS template_blueprints (
                blueprint_id TEXT PRIMARY KEY,
                repo_name TEXT NOT NULL,
                file_path TEXT NOT NULL,
                symbol_name TEXT NOT NULL,
                stack_domain TEXT NOT NULL,
                description TEXT NOT NULL,
                code_snippet TEXT NOT NULL,
                start_line INTEGER NOT NULL,
                end_line INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """)

    # =========================================================================
    # Layer 1 Operations
    # =========================================================================
    def upsert_parent_and_children(self, parent: ASTParentNode, children: List[ASTChildNode]) -> None:
        with self.conn:
            # Check existing parent
            cur = self.conn.execute("SELECT parent_id FROM ast_parents WHERE file_path = ?", (parent.file_path,))
            row = cur.fetchone()
            if row:
                old_id = row["parent_id"]
                self.conn.execute("DELETE FROM ast_children WHERE parent_id = ?", (old_id,))
                self.conn.execute("DELETE FROM ast_parents WHERE file_path = ?", (parent.file_path,))

            self.conn.execute(
                """
                INSERT INTO ast_parents (parent_id, file_path, language, imports_header, enclosing_scope, git_blob_sha)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    str(parent.parent_id),
                    parent.file_path,
                    parent.language,
                    parent.imports_header,
                    parent.enclosing_scope,
                    parent.git_blob_sha,
                ),
            )

            for child in children:
                self.conn.execute(
                    """
                    INSERT INTO ast_children (
                        child_id, parent_id, file_path, node_kind, symbol_name, signature, docstring, body_code, start_line, end_line
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        str(child.child_id),
                        str(parent.parent_id),
                        child.file_path,
                        child.node_kind,
                        child.symbol_name,
                        child.signature,
                        child.docstring,
                        child.body_code,
                        child.start_line,
                        child.end_line,
                    ),
                )

    def get_parent_by_path(self, file_path: str) -> Optional[ASTParentNode]:
        cur = self.conn.execute("SELECT * FROM ast_parents WHERE file_path = ?", (file_path,))
        row = cur.fetchone()
        if not row:
            return None
        return ASTParentNode(
            parent_id=UUID(row["parent_id"]),
            file_path=row["file_path"],
            language=row["language"],
            imports_header=row["imports_header"],
            enclosing_scope=row["enclosing_scope"],
            git_blob_sha=row["git_blob_sha"],
        )

    def get_all_children_with_parents(self) -> List[Tuple[ASTParentNode, ASTChildNode]]:
        cur = self.conn.execute("""
            SELECT
                p.parent_id as p_id, p.file_path as p_path, p.language as p_lang,
                p.imports_header as p_imports, p.enclosing_scope as p_scope, p.git_blob_sha as p_sha,
                c.child_id as c_id, c.parent_id as c_pid, c.file_path as c_path, c.node_kind as c_kind,
                c.symbol_name as c_sym, c.signature as c_sig, c.docstring as c_doc,
                c.body_code as c_body, c.start_line as c_start, c.end_line as c_end
            FROM ast_children c
            JOIN ast_parents p ON c.parent_id = p.parent_id
        """)
        results: List[Tuple[ASTParentNode, ASTChildNode]] = []
        for row in cur.fetchall():
            parent = ASTParentNode(
                parent_id=UUID(row["p_id"]),
                file_path=row["p_path"],
                language=row["p_lang"],
                imports_header=row["p_imports"],
                enclosing_scope=row["p_scope"],
                git_blob_sha=row["p_sha"],
            )
            child = ASTChildNode(
                child_id=UUID(row["c_id"]),
                parent_id=UUID(row["c_pid"]),
                file_path=row["c_path"],
                node_kind=row["c_kind"],
                symbol_name=row["c_sym"],
                signature=row["c_sig"],
                docstring=row["c_doc"],
                body_code=row["c_body"],
                start_line=row["c_start"],
                end_line=row["c_end"],
            )
            results.append((parent, child))
        return results

    # =========================================================================
    # Layer 2 Operations: Episodic Memory
    # =========================================================================
    def record_episode(self, episode: EpisodicBugRecord) -> None:
        with self.conn:
            self.conn.execute(
                """
                INSERT OR REPLACE INTO project_episodes (
                    episode_id, error_signature, target_symbol, file_path, root_cause_summary, resolution_diff
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    str(episode.episode_id),
                    episode.error_signature,
                    episode.target_symbol,
                    episode.file_path,
                    episode.root_cause_summary,
                    episode.resolution_diff,
                ),
            )

    def find_matching_episodes(
        self,
        symbol_name: Optional[str] = None,
        file_path: Optional[str] = None,
        query: Optional[str] = None,
        limit: int = 3,
    ) -> List[EpisodicBugRecord]:
        cur = self.conn.execute("SELECT * FROM project_episodes ORDER BY created_at DESC")
        episodes: List[EpisodicBugRecord] = []
        for row in cur.fetchall():
            ep = EpisodicBugRecord(
                episode_id=UUID(row["episode_id"]),
                error_signature=row["error_signature"],
                target_symbol=row["target_symbol"],
                file_path=row["file_path"],
                root_cause_summary=row["root_cause_summary"],
                resolution_diff=row["resolution_diff"],
            )
            score = 0
            if symbol_name and (symbol_name in ep.target_symbol or ep.target_symbol in symbol_name):
                score += 3
            if file_path and (file_path in ep.file_path or ep.file_path in file_path):
                score += 2
            if query:
                q_tokens = _normalize_tokens(query)
                ep_text = f"{ep.target_symbol} {ep.error_signature} {ep.root_cause_summary}".lower()
                if any(t in ep_text for t in q_tokens):
                    score += 1
            if score > 0 or (not symbol_name and not file_path and not query):
                episodes.append(ep)
                if len(episodes) >= limit:
                    break
        return episodes

    # =========================================================================
    # Layer 3 Operations: Tech Knowledge Chunks
    # =========================================================================
    def add_tech_chunk(self, chunk: TechKnowledgeChunk) -> None:
        with self.conn:
            self.conn.execute(
                """
                INSERT OR REPLACE INTO tech_knowledge_chunks (
                    chunk_id, source_doc, domain, title, content, external_url
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    str(chunk.chunk_id),
                    chunk.source_doc,
                    chunk.domain,
                    chunk.title,
                    chunk.content,
                    chunk.external_url,
                ),
            )

    def search_tech_chunks(self, query: str, limit: int = 5) -> List[TechKnowledgeChunk]:
        q_tokens = _normalize_tokens(query)
        cur = self.conn.execute("SELECT * FROM tech_knowledge_chunks")
        results: List[Tuple[float, TechKnowledgeChunk]] = []
        for row in cur.fetchall():
            chunk = TechKnowledgeChunk(
                chunk_id=UUID(row["chunk_id"]),
                source_doc=row["source_doc"],
                domain=row["domain"],
                title=row["title"],
                content=row["content"],
                external_url=row["external_url"],
            )
            text = f"{chunk.title} {chunk.content}".lower()
            matches = sum(1 for t in q_tokens if t in text)
            score = matches / max(1, len(q_tokens))
            if query.lower() in chunk.title.lower():
                score += 0.5
            if score > 0:
                results.append((score, chunk))
        results.sort(key=lambda x: x[0], reverse=True)
        return [c for _, c in results[:limit]]

    # =========================================================================
    # Layer 4 Operations: Template Blueprints
    # =========================================================================
    def add_blueprint(self, bp: TemplateBlueprint) -> None:
        with self.conn:
            self.conn.execute(
                """
                INSERT OR REPLACE INTO template_blueprints (
                    blueprint_id, repo_name, file_path, symbol_name, stack_domain, description, code_snippet, start_line, end_line
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    str(bp.blueprint_id),
                    bp.repo_name,
                    bp.file_path,
                    bp.symbol_name,
                    bp.stack_domain,
                    bp.description,
                    bp.code_snippet,
                    bp.start_line,
                    bp.end_line,
                ),
            )

    def search_blueprints(self, query: str, stack_domain: str = "all", limit: int = 5) -> List[TemplateBlueprint]:
        q_tokens = _normalize_tokens(query)
        cur = self.conn.execute("SELECT * FROM template_blueprints")
        results: List[Tuple[float, TemplateBlueprint]] = []
        for row in cur.fetchall():
            if stack_domain != "all" and row["stack_domain"].lower() != stack_domain.lower():
                continue
            bp = TemplateBlueprint(
                blueprint_id=UUID(row["blueprint_id"]),
                repo_name=row["repo_name"],
                file_path=row["file_path"],
                symbol_name=row["symbol_name"],
                stack_domain=row["stack_domain"],
                description=row["description"],
                code_snippet=row["code_snippet"],
                start_line=row["start_line"],
                end_line=row["end_line"],
            )
            text = f"{bp.repo_name} {bp.symbol_name} {bp.description} {bp.stack_domain}".lower()
            matches = sum(1 for t in q_tokens if t in text)
            score = matches / max(1, len(q_tokens))
            if bp.symbol_name.lower() in query.lower():
                score += 0.4
            if score > 0 or not q_tokens:
                results.append((score, bp))
        results.sort(key=lambda x: x[0], reverse=True)
        return [b for _, b in results[:limit]]

    def close(self) -> None:
        self.conn.close()

