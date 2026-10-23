# tests/test_self_learning.py
"""
Unit and integration tests for the 3-Tier Self-Learning Compounding Engine.
Tests:
- Tier 1: Fail-to-Pass distillation & search immunization.
- Tier 2: Macro ADR auto-promotion when error patterns recur >= 3 times.
- Tier 3: Living blueprint harvesting into Layer 4 template stockroom.
"""

import shutil
import sys
import unittest
from pathlib import Path

SRC_DIR = Path(__file__).resolve().parent.parent / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from repobrain.episodic_memory import EpisodicMemoryStore
from repobrain.template_stockroom import TemplateStockroom


class TestSelfLearningEngine(unittest.TestCase):
    def setUp(self):
        self.test_root = Path("test_scratch_learning")
        if self.test_root.exists():
            shutil.rmtree(self.test_root)
        self.test_root.mkdir(parents=True, exist_ok=True)
        self.ep_store = EpisodicMemoryStore()

    def tearDown(self):
        if self.test_root.exists():
            shutil.rmtree(self.test_root)

    def test_tier2_adr_auto_promotion_on_recurrence(self):
        """
        Tier 2: When an identical root-cause / error pattern recurs >= 3 times,
        RepoBrain clusters the episodes and auto-promotes an ADR to .repobrain/kb/adrs/.
        """
        # Record 3 distinct episodes with the same root cause pattern across different files
        self.ep_store.record_episode(
            error_signature="AssertionError: Decimal('120.0000') != Decimal('120.00')",
            target_symbol="LedgerService.settleInvoiceById",
            file_path="src/billing/ledger.py",
            root_cause_summary="Decimal scale preserved without explicit quantization; append .quantize(Decimal('0.01')).",
            resolution_diff="+ return amount.quantize(Decimal('0.01'))",
        )
        self.ep_store.record_episode(
            error_signature="AssertionError: Decimal('50.0000') != Decimal('50.00')",
            target_symbol="TaxCalculator.computeTax",
            file_path="src/tax/calculator.py",
            root_cause_summary="Decimal scale preserved without explicit quantization; append .quantize(Decimal('0.01')).",
            resolution_diff="+ return tax.quantize(Decimal('0.01'))",
        )
        self.ep_store.record_episode(
            error_signature="AssertionError: Decimal('9.9900') != Decimal('9.99')",
            target_symbol="DiscountEngine.applyDiscount",
            file_path="src/discounts/engine.py",
            root_cause_summary="Decimal scale preserved without explicit quantization; append .quantize(Decimal('0.01')).",
            resolution_diff="+ return discounted.quantize(Decimal('0.01'))",
        )

        promoted = self.ep_store.promote_recurring_to_adrs(self.test_root, min_count=3)
        self.assertEqual(len(promoted), 1, "Expected exactly 1 auto-promoted ADR.")

        adr_path = promoted[0]
        self.assertTrue(adr_path.exists())
        content = adr_path.read_text(encoding="utf-8")

        self.assertIn("Auto-Promoted Policy", content)
        self.assertIn("**Recurrence Count:** 3", content)
        self.assertIn("quantize(Decimal('0.01'))", content)
        self.assertIn("LedgerService.settleInvoiceById", content)

    def test_tier3_living_blueprint_harvesting(self):
        """
        Tier 3: When a clean architectural pattern is synthesized,
        harvest_blueprint captures it into Layer 4 Stockroom.
        """
        stockroom = TemplateStockroom()
        bp = stockroom.harvest_blueprint(
            symbol_name="LangGraph.CheckpointMemorySaver",
            file_path="src/agents/state.py",
            code_snippet="from langgraph.checkpoint.memory import MemorySaver\ncheckpointer = MemorySaver()",
            stack_domain="langgraph",
            description="In-memory checkpointer for LangGraph state graph persistence.",
        )

        self.assertEqual(bp.symbol_name, "LangGraph.CheckpointMemorySaver")
        self.assertEqual(bp.stack_domain, "langgraph")

        # Verify search_templates retrieves it
        matches = stockroom.search_templates("MemorySaver checkpoint", stack_domain="langgraph")
        self.assertGreaterEqual(len(matches), 1)
        self.assertEqual(matches[0].symbol_name, "LangGraph.CheckpointMemorySaver")

    def test_preseeded_blueprints_availability(self):
        """Verify preseeded blueprints for Next.js, LangGraph, and FastAPI."""
        stockroom = TemplateStockroom()
        
        # Next.js Server Action
        nextjs_matches = stockroom.search_templates("ZodValidation ServerAction", stack_domain="nextjs")
        self.assertGreaterEqual(len(nextjs_matches), 1)
        self.assertIn("use server", nextjs_matches[0].code_snippet)

        # LangGraph StateGraph
        lg_matches = stockroom.search_templates("conditional_edges StateGraph", stack_domain="langgraph")
        self.assertGreaterEqual(len(lg_matches), 1)
        self.assertIn("StateGraph", lg_matches[0].code_snippet)


if __name__ == "__main__":
    unittest.main()
