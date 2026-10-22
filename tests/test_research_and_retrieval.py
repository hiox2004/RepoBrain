# tests/test_research_and_retrieval.py
"""
Test Suite for Slice 2: Hybrid RRF, Episodic Memory, ResearchBrain, and Template Stockroom.
Compatible with both pytest and python -m unittest.
"""

import sys
import unittest
from pathlib import Path

# Ensure src is on sys.path
SRC_DIR = Path(__file__).resolve().parent.parent / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from repobrain.episodic_memory import EpisodicMemoryStore
from repobrain.hybrid_retriever import (
    HybridCodebaseRetriever,
    build_disjunction_tsquery,
    normalize_code_identifiers_py,
)
from repobrain.research_brain import ResearchBrainEngine
from repobrain.template_stockroom import TemplateStockroom


class TestResearchAndRetrieval(unittest.TestCase):
    def test_split_token_identifier_normalization(self):
        # Guardrail #3: camelCase, PascalCase, snake_case splitting
        raw = "settleInvoiceById"
        normalized = normalize_code_identifiers_py(raw)
        self.assertIn("settleInvoiceById", normalized)
        self.assertIn("settle", normalized)
        self.assertIn("invoice", normalized)
        self.assertIn("by", normalized)
        self.assertIn("id", normalized)

    def test_disjunction_tsquery_generation(self):
        # Guardrail #4: OR-based tsquery over tokens length > 1
        query = "settleInvoiceById Decimal quantization"
        ts_q, tokens = build_disjunction_tsquery(query)
        self.assertIn(" | ", ts_q)
        self.assertIn("settleinvoicebyid", [t.lower() for t in tokens])
        self.assertIn("decimal", [t.lower() for t in tokens])

    def test_episodic_memory_distillation(self):
        # Layer 2: Episodic Diagnostic Memory
        store = EpisodicMemoryStore()
        ep = store.record_episode(
            error_signature="AssertionError: Decimal('120.0000') != Decimal('120.00')",
            target_symbol="LedgerService.settleInvoiceById",
            file_path="src/billing/ledger.py",
            root_cause_summary="Decimal scale preserved without explicit quantization; append .quantize(Decimal('0.01')).",
            resolution_diff="""--- a/src/billing/ledger.py\n+++ b/src/billing/ledger.py\n@@ -21 +21 @@\n- return req.subtotal * (Decimal("1.00") - self.tax_rate)\n+ return (req.subtotal * (Decimal("1.00") + self.tax_rate)).quantize(Decimal("0.01"))""",
        )

        self.assertEqual(ep.target_symbol, "LedgerService.settleInvoiceById")
        matches = store.find_matching_episodes(symbol_name="settleInvoiceById")
        self.assertEqual(len(matches), 1)
        self.assertIn(".quantize", matches[0].root_cause_summary)

    def test_research_brain_crag_engine(self):
        # Layer 3: Conceptual ResearchBrain with local KB
        test_root = Path("test_scratch_kb")
        engine = ResearchBrainEngine(repo_root=test_root)
        engine.add_local_knowledge(
            title="FastAPI OAuth2 Dependency Injection",
            content="Use Annotated[str, Depends(oauth2_scheme)] to enforce strict token decoding and 401 handling.",
            source_doc="rfcs/fastapi_auth.md",
        )

        brief = engine.research_technology("FastAPI OAuth2 Dependency Injection")
        self.assertGreaterEqual(brief.confidence_score, 0.75)
        self.assertEqual(brief.source, "local_kb")
        self.assertIn("oauth2_scheme", brief.summary_markdown)

        # Cleanup scratch dir
        import shutil
        if test_root.exists():
            shutil.rmtree(test_root)

    def test_template_stockroom_dual_advisory(self):
        # Layer 4: GitHub Template Stockroom
        stockroom = TemplateStockroom()
        results = stockroom.search_templates("fastapi oauth2 dependency", stack_domain="fastapi")
        self.assertGreaterEqual(len(results), 1)
        bp = results[0]
        self.assertEqual(bp.repo_name, "tiangolo/full-stack-fastapi-template")
        advisory_md = bp.to_advisory_markdown()
        self.assertIn("tiangolo/full-stack-fastapi-template", advisory_md)
        self.assertIn("get_current_user", advisory_md)

    def test_hybrid_rrf_retriever_search_with_episodes(self):
        # Full Two-Stage RRF + Layer 2 Episode Injection
        retriever = HybridCodebaseRetriever()
        retriever.episodic_store.clear()
        code = '''from decimal import Decimal
from fastapi import APIRouter

router = APIRouter()

class InvoiceRequest:
    subtotal: Decimal

class LedgerService:
    @router.post("/v1/settle")
    def settleInvoiceById(self, req: InvoiceRequest) -> Decimal:
        """Calculates settlement."""
        return req.subtotal * Decimal("1.20")
'''
        retriever.index_code_string(code, virtual_path="src/billing/ledger.py", language="python")

        # Record matching episode
        retriever.episodic_store.record_episode(
            error_signature="AssertionError: mismatch",
            target_symbol="LedgerService.settleInvoiceById",
            file_path="src/billing/ledger.py",
            root_cause_summary="Use .quantize(Decimal('0.01')) for currency settlements.",
            resolution_diff="--- patch",
        )

        results = retriever.search("settleInvoiceById decimal", top_k=3, include_episodes=True)
        self.assertGreaterEqual(len(results), 1)
        top_match = results[0]
        self.assertEqual(top_match.symbol_name, "LedgerService.settleInvoiceById")
        self.assertEqual(len(top_match.related_episodes), 1)

        xml_block = top_match.to_xml_prompt_block()
        self.assertIn("<ast_context", xml_block)
        self.assertIn("<past_episodic_fix", xml_block)
        self.assertIn(".quantize", xml_block)


if __name__ == "__main__":
    unittest.main()
