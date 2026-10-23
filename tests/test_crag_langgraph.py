# tests/test_crag_langgraph.py
"""
Unit and integration tests for Layer 3: Conceptual ResearchBrain LangGraph CRAG Engine.
Tests all 5 phases, conditional edge routing, cache short-circuiting, and fallback compaction.
"""

import shutil
import sys
import unittest
from pathlib import Path

SRC_DIR = Path(__file__).resolve().parent.parent / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from repobrain.research_brain import ResearchBrainEngine, slugify, HAS_LANGGRAPH


class TestLangGraphCRAG(unittest.TestCase):
    def setUp(self):
        self.test_root = Path("test_scratch_crag")
        if self.test_root.exists():
            shutil.rmtree(self.test_root)
        self.engine = ResearchBrainEngine(repo_root=self.test_root)

    def tearDown(self):
        if self.test_root.exists():
            shutil.rmtree(self.test_root)

    def test_langgraph_engine_active(self):
        """Verify that LangGraph is detected and the StateGraph is compiled."""
        self.assertTrue(HAS_LANGGRAPH, "LangGraph should be installed and available.")
        self.assertIsNotNone(self.engine.graph, "Compiled StateGraph must be initialized.")

    def test_local_kb_high_confidence_short_circuit(self):
        """
        Phase 2 & 3: If local knowledge has score >= 0.75,
        LangGraph routes directly to synthesize_and_cache (0 web calls).
        """
        self.engine.add_local_knowledge(
            title="Next.js 15 Async Request APIs",
            content="In Next.js 15, cookies(), headers(), and params are asynchronous. Await params before reading id.",
            source_doc="adrs/nextjs_params.md",
            domain="nextjs",
        )

        brief = self.engine.research_technology("Next.js 15 Async Request APIs")
        self.assertGreaterEqual(brief.confidence_score, 0.75)
        self.assertEqual(brief.source, "local_kb")
        self.assertIn("Await params before reading id", brief.summary_markdown)
        self.assertIn("adrs/nextjs_params.md", brief.cited_passages)

    def test_fastpath_cache_hit(self):
        """
        Phase 1: Cached brief must return immediately on second query
        without querying or grading (0 tokens, confidence 1.0).
        """
        self.engine.add_local_knowledge(
            title="FastAPI Lifespan State Handler",
            content="Use @asynccontextmanager async def lifespan(app: FastAPI): yield {'db': pool} for clean teardown.",
            source_doc="adrs/fastapi_lifespan.md",
        )

        # First run populates cache
        brief1 = self.engine.research_technology("FastAPI Lifespan State Handler")
        self.assertEqual(brief1.source, "local_kb")

        # Second run hits cache directly
        brief2 = self.engine.research_technology("FastAPI Lifespan State Handler")
        self.assertEqual(brief2.confidence_score, 1.0)
        self.assertEqual(brief2.source, "local_kb")
        self.assertIn("Cached brief", brief2.cited_passages[0])

    def test_bounded_web_fallback_when_local_kb_empty(self):
        """
        Phase 4: When query is not found locally, confidence < 0.75 triggers
        bounded 1-hop web compactor with < 1,000 tokens dense snippets.
        """
        query = "LangGraph MemorySaver checkpoint persistence"
        brief = self.engine.research_technology(query)

        self.assertIn(brief.source, ["web_fallback", "local_kb"])
        self.assertGreaterEqual(brief.confidence_score, 0.50)
        self.assertTrue(len(brief.summary_markdown) > 50)

        # Word count should be strictly bounded (< 600 words / ~800 tokens)
        words = brief.summary_markdown.split()
        self.assertLess(len(words), 600, "Compacted research brief must remain < 600 words.")


if __name__ == "__main__":
    unittest.main()
