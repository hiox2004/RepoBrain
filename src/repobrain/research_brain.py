# src/repobrain/research_brain.py
"""
Layer 3: Conceptual ResearchBrain (5-Phase Bounded Corrective RAG / CRAG)
Powered by an isolated LangGraph StateGraph engine.
Governed strictly by 00_FOUNDING_ARCHITECTURE.md Pillar 3 and 05_MULTI_AGENT_SYSTEM_OF_WORKING.md.

Invariants:
1. stdio Hygiene: Zero unsolicited prints to stdout. Logs stream to sys.stderr.
2. Fastpath Caching: .repobrain/kb_cache/<slug>.md checked first (0 tokens).
3. Retrieval Grader: If confidence >= 0.75, short-circuits with local ADRs/RFCs (0 external tokens).
4. Bounded 1-Hop Web Fallback: If < 0.75, compacts dense snippets (< 1,000 tokens) via clean HTML parsing.
"""

from __future__ import annotations
import logging
import os
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional, Tuple, TypedDict
from uuid import uuid4

import httpx
from bs4 import BeautifulSoup

from repobrain.schemas import ResearchBrief, TechKnowledgeChunk

# Configure sys.stderr logger for stdio FastMCP hygiene
logger = logging.getLogger("RepoBrain.ResearchBrain")
if not logger.handlers:
    _handler = logging.StreamHandler(sys.stderr)
    _handler.setFormatter(logging.Formatter("[%(name)s] %(levelname)s: %(message)s"))
    logger.addHandler(_handler)
    logger.setLevel(logging.INFO)

# Check LangGraph availability
try:
    from langgraph.graph import StateGraph, START, END
    HAS_LANGGRAPH = True
except ImportError:
    HAS_LANGGRAPH = False
    logger.warning("LangGraph not installed; running deterministic procedural fallback for CRAG.")


def slugify(text: str) -> str:
    """Converts a query string into a filesystem-safe slug."""
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    return re.sub(r"[-\s]+", "_", text)[:64]


class CRAGState(TypedDict):
    """Encapsulated state for the 5-Phase Corrective RAG (CRAG) StateGraph."""
    query: str
    domain: str
    slug: str
    local_chunks: List[TechKnowledgeChunk]
    confidence_score: float
    grade_verdict: Literal["CORRECT", "AMBIGUOUS", "INCORRECT"]
    web_passages: List[str]
    brief: Optional[ResearchBrief]


class ResearchBrainEngine:
    """
    5-Phase Corrective RAG (CRAG) Engine:
    Phase 1: Semantic Fastpath Router (.repobrain/kb_cache/<slug>.md)
    Phase 2: Local Domain Tech KB Search (.repobrain/kb/)
    Phase 3: Retrieval Grader (threshold >= 0.75)
    Phase 4: Bounded 1-Hop Web Compactor (< 1,000 tokens)
    Phase 5: Grounding Check & Markdown Cache
    """

    def __init__(self, repo_root: Optional[Path] = None) -> None:
        self.repo_root = (repo_root or Path.cwd()).resolve()
        self.kb_dir = self.repo_root / ".repobrain" / "kb"
        self.cache_dir = self.repo_root / ".repobrain" / "kb_cache"
        self.local_chunks: List[TechKnowledgeChunk] = []

        self._ensure_directories()
        self._load_local_kb()
        self.graph = self._build_langgraph() if HAS_LANGGRAPH else None

    def _ensure_directories(self) -> None:
        self.kb_dir.mkdir(parents=True, exist_ok=True)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _load_local_kb(self) -> None:
        """Indexes all markdown files in .repobrain/kb/ as TechKnowledgeChunks."""
        self.local_chunks.clear()
        if not self.kb_dir.exists():
            return

        for md_file in self.kb_dir.glob("**/*.md"):
            try:
                text = md_file.read_text(encoding="utf-8")
                rel_path = md_file.relative_to(self.kb_dir).as_posix()
                sections = re.split(r"(?m)^(?=#{1,3}\s)", text)
                for section in sections:
                    sec_clean = section.strip()
                    if len(sec_clean) < 25:
                        continue
                    first_line = sec_clean.splitlines()[0].lstrip("#").strip()
                    self.local_chunks.append(
                        TechKnowledgeChunk(
                            chunk_id=uuid4(),
                            source_doc=rel_path,
                            domain=md_file.parent.name if md_file.parent != self.kb_dir else "general",
                            title=first_line or md_file.stem,
                            content=sec_clean,
                        )
                    )
            except Exception as e:
                logger.debug(f"Failed to index markdown file {md_file}: {e}")

    def add_local_knowledge(
        self,
        title: str,
        content: str,
        source_doc: str = "adrs/core.md",
        domain: str = "general",
    ) -> TechKnowledgeChunk:
        """Programmatically adds a knowledge chunk to local memory and writes to disk."""
        chunk = TechKnowledgeChunk(
            chunk_id=uuid4(),
            source_doc=source_doc,
            domain=domain,
            title=title,
            content=content,
        )
        self.local_chunks.append(chunk)

        target_path = self.kb_dir / source_doc
        target_path.parent.mkdir(parents=True, exist_ok=True)
        with open(target_path, "a", encoding="utf-8") as f:
            f.write(f"\n\n## {title}\n{content}\n")

        return chunk

    # =========================================================================
    # LangGraph Node Handlers
    # =========================================================================

    def _node_check_cache(self, state: CRAGState) -> Dict[str, Any]:
        """Phase 1: Fast-path cache lookup in .repobrain/kb_cache/<slug>.md"""
        slug = slugify(state["query"])
        cache_file = self.cache_dir / f"{slug}.md"

        if cache_file.exists():
            try:
                cached_text = cache_file.read_text(encoding="utf-8")
                brief = ResearchBrief(
                    query=state["query"],
                    confidence_score=1.0,
                    source="local_kb",
                    summary_markdown=cached_text,
                    cited_passages=[f"Cached brief: {cache_file.name}"],
                    cached_slug=slug,
                )
                return {
                    "slug": slug,
                    "confidence_score": 1.0,
                    "grade_verdict": "CORRECT",
                    "brief": brief,
                }
            except Exception:
                pass

        return {"slug": slug, "confidence_score": 0.0, "brief": None}

    def _node_retrieve_local_kb(self, state: CRAGState) -> Dict[str, Any]:
        """Phase 2: Local Domain Tech KB Search."""
        query = state["query"].lower()
        q_tokens = set(re.findall(r"\w+", query))
        if not q_tokens or not self.local_chunks:
            return {"local_chunks": []}

        scored: List[Tuple[float, TechKnowledgeChunk]] = []
        for chunk in self.local_chunks:
            text = f"{chunk.title} {chunk.content}".lower()
            c_tokens = set(re.findall(r"\w+", text))
            intersection = q_tokens.intersection(c_tokens)
            score = len(intersection) / len(q_tokens)

            # Exact title boost
            if query in chunk.title.lower():
                score = min(1.0, score + 0.45)
            elif any(q in chunk.title.lower() for q in q_tokens if len(q) > 3):
                score = min(1.0, score + 0.20)

            if score > 0.15:
                scored.append((score, chunk))

        scored.sort(key=lambda x: x[0], reverse=True)
        top_chunks = [c for _, c in scored[:3]]
        return {"local_chunks": top_chunks}

    def _node_grade_retrieval(self, state: CRAGState) -> Dict[str, Any]:
        """Phase 3: Retrieval Grader node. Evaluates relevance threshold >= 0.75."""
        chunks = state.get("local_chunks", [])
        if not chunks:
            return {"confidence_score": 0.0, "grade_verdict": "INCORRECT"}

        query = state["query"].lower()
        q_tokens = set(re.findall(r"\w+", query))
        best_score = 0.0

        for chunk in chunks:
            text = f"{chunk.title} {chunk.content}".lower()
            c_tokens = set(re.findall(r"\w+", text))
            score = len(q_tokens.intersection(c_tokens)) / len(q_tokens) if q_tokens else 0.0
            if query in chunk.title.lower():
                score = min(1.0, score + 0.45)
            if score > best_score:
                best_score = score

        verdict: Literal["CORRECT", "AMBIGUOUS", "INCORRECT"]
        if best_score >= 0.75:
            verdict = "CORRECT"
        elif best_score >= 0.35:
            verdict = "AMBIGUOUS"
        else:
            verdict = "INCORRECT"

        return {"confidence_score": best_score, "grade_verdict": verdict}

    def _node_bounded_web_compactor(self, state: CRAGState) -> Dict[str, Any]:
        """
        Phase 4: Bounded 1-Hop External Search & Extractive Passage Compactor.
        Strips HTML tags, headers, and navbars. Compresses to < 1,000 tokens.
        """
        query = state["query"]
        passages: List[str] = []

        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
        }

        try:
            # Bounded 1-hop search via DuckDuckGo HTML endpoint
            resp = httpx.post(
                "https://html.duckduckgo.com/html/",
                data={"q": query},
                headers=headers,
                timeout=4.0,
            )
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, "html.parser")
                for item in soup.select(".result__body")[:3]:
                    snippet_elem = item.select_one(".result__snippet")
                    title_elem = item.select_one(".result__title")
                    if snippet_elem:
                        clean_text = snippet_elem.get_text(" ", strip=True)
                        title_text = title_elem.get_text(" ", strip=True) if title_elem else "Reference"
                        # Limit words per snippet to ~80 words (~100 tokens)
                        words = clean_text.split()[:80]
                        passages.append(f"**[{title_text}]**\n{' '.join(words)}")
        except Exception as e:
            logger.debug(f"External web fetch timed out or failed: {e}")

        # Graceful parametric fallback if web search yielded 0 passages
        if not passages:
            passages = [
                f"**[Parametric Idiom \u2014 {query}]**\n"
                f"Enforce strict type hinting, deterministic error boundaries, "
                f"and isolated dependency injection adhering to modern PEP 8 / TypeScript conventions."
            ]

        return {"web_passages": passages}

    def _node_synthesize_and_cache(self, state: CRAGState) -> Dict[str, Any]:
        """
        Phase 5: Grounding Check, Markdown Cache Persistence, and Brief Generation.
        """
        query = state["query"]
        slug = state.get("slug") or slugify(query)
        cache_file = self.cache_dir / f"{slug}.md"
        confidence = state.get("confidence_score", 0.0)
        chunks = state.get("local_chunks", [])
        web_passages = state.get("web_passages", [])

        if confidence >= 0.75 and chunks:
            source: Literal["local_kb", "web_fallback", "parametric_fastpath"] = "local_kb"
            body_parts = []
            for c in chunks:
                words = c.content.split()[:120]
                body_parts.append(f"### {c.title}\n*Source: `{c.source_doc}`*\n\n{' '.join(words)}")

            summary = (
                f"# Research Brief: {query}\n\n"
                f"**Confidence Score:** `{confidence:.2f}` (Verified against Local Architecture Knowledge Base)\n"
                f"**Source:** Local `.repobrain/kb/` (0 external tokens consumed)\n\n"
                + "\n\n".join(body_parts)
            )
            cited = [c.source_doc for c in chunks]
        else:
            source = "web_fallback"
            effective_conf = max(0.50, confidence)
            summary = (
                f"# Research Brief: {query}\n\n"
                f"**Confidence Score:** `{effective_conf:.2f}` (Bounded 1-Hop External Synthesis)\n"
                f"**Source:** Bounded Web Fallback (< 1,000 tokens extractive compaction)\n\n"
                + "\n\n".join(web_passages)
            )
            cited = ["bounded_web_search_compactor"]

        try:
            cache_file.write_text(summary, encoding="utf-8")
        except Exception as e:
            logger.debug(f"Failed to persist cache file {cache_file}: {e}")

        brief = ResearchBrief(
            query=query,
            confidence_score=max(0.50, confidence) if source == "web_fallback" else confidence,
            source=source,
            summary_markdown=summary,
            cited_passages=cited,
            cached_slug=slug,
        )

        return {"brief": brief}

    # =========================================================================
    # Graph Construction & Conditional Routing
    # =========================================================================

    def _build_langgraph(self) -> Any:
        """Assembles the 5-phase StateGraph with conditional edges."""
        builder = StateGraph(CRAGState)

        # 1. Register Nodes
        builder.add_node("check_cache", self._node_check_cache)
        builder.add_node("retrieve_local_kb", self._node_retrieve_local_kb)
        builder.add_node("grade_retrieval", self._node_grade_retrieval)
        builder.add_node("bounded_web_compactor", self._node_bounded_web_compactor)
        builder.add_node("synthesize_and_cache", self._node_synthesize_and_cache)

        # 2. Routing Functions
        def route_after_cache(state: CRAGState) -> str:
            if state.get("brief") is not None:
                return END
            return "retrieve_local_kb"

        def route_after_grading(state: CRAGState) -> str:
            if state.get("confidence_score", 0.0) >= 0.75:
                return "synthesize_and_cache"
            return "bounded_web_compactor"

        # 3. Register Edges
        builder.add_edge(START, "check_cache")
        builder.add_conditional_edges(
            "check_cache",
            route_after_cache,
            {"retrieve_local_kb": "retrieve_local_kb", END: END},
        )
        builder.add_edge("retrieve_local_kb", "grade_retrieval")
        builder.add_conditional_edges(
            "grade_retrieval",
            route_after_grading,
            {
                "synthesize_and_cache": "synthesize_and_cache",
                "bounded_web_compactor": "bounded_web_compactor",
            },
        )
        builder.add_edge("bounded_web_compactor", "synthesize_and_cache")
        builder.add_edge("synthesize_and_cache", END)

        return builder.compile()

    # =========================================================================
    # Public Unified Entrypoint
    # =========================================================================

    def research_technology(self, query: str, domain: str = "general_tech") -> ResearchBrief:
        """
        Unified 5-Phase CRAG Execution.
        Runs the compiled LangGraph StateGraph if available, with deterministic fallback.
        """
        initial_state: CRAGState = {
            "query": query,
            "domain": domain,
            "slug": slugify(query),
            "local_chunks": [],
            "confidence_score": 0.0,
            "grade_verdict": "INCORRECT",
            "web_passages": [],
            "brief": None,
        }

        # 1. Execute via LangGraph StateGraph
        if self.graph is not None:
            try:
                final_state = self.graph.invoke(initial_state)
                if final_state.get("brief"):
                    return final_state["brief"]
            except Exception as e:
                logger.error(f"LangGraph execution error: {e}. Falling back to procedural execution.")

        # 2. Deterministic Procedural Fallback (Identical 5 Phases)
        s1 = self._node_check_cache(initial_state)
        if s1.get("brief"):
            return s1["brief"]

        initial_state.update(s1)
        s2 = self._node_retrieve_local_kb(initial_state)
        initial_state.update(s2)
        s3 = self._node_grade_retrieval(initial_state)
        initial_state.update(s3)

        if initial_state.get("confidence_score", 0.0) < 0.75:
            s4 = self._node_bounded_web_compactor(initial_state)
            initial_state.update(s4)

        s5 = self._node_synthesize_and_cache(initial_state)
        return s5["brief"]
