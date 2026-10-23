# tests/test_blast_radius.py
"""
Unit tests for the Blast-Radius Dependency Graph Analyzer.
Tests caller detection, test suite association, risk level scoring, and advisory generation.
"""

import sys
import unittest
from pathlib import Path

SRC_DIR = Path(__file__).resolve().parent.parent / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from repobrain.hybrid_retriever import HybridCodebaseRetriever


class TestBlastRadius(unittest.TestCase):
    def setUp(self):
        self.retriever = HybridCodebaseRetriever()

    def test_blast_radius_settle_invoice(self):
        """Verify blast radius calculation for LedgerService.settleInvoiceById."""
        result = self.retriever.compute_blast_radius("LedgerService.settleInvoiceById")

        self.assertEqual(result["symbol_name"], "LedgerService.settleInvoiceById")
        self.assertTrue(result["found_target"])
        self.assertIn("ledger.py", result["file_path"])

        # Should identify test_bounded_harness.py in associated_tests
        tests = [t for t in result["associated_tests"] if "test_bounded_harness.py" in t]
        self.assertGreaterEqual(len(tests), 1, "Should detect tests/test_bounded_harness.py")

        # Advisory must contain actionable instructions
        self.assertIn("advisory", result)
        self.assertIn("settleInvoiceById", result["advisory"])
        self.assertIn(result["risk_level"], ["HIGH", "MODERATE", "LOW"])

    def test_blast_radius_invoice_request_type(self):
        """Verify blast radius for schema InvoiceRequest which is used by settleInvoiceById."""
        result = self.retriever.compute_blast_radius("InvoiceRequest")

        self.assertEqual(result["symbol_name"], "InvoiceRequest")
        self.assertTrue(result["found_target"])

        # settleInvoiceById accepts InvoiceRequest, so it should be listed in callers or body match
        self.assertGreaterEqual(result["callers_count"], 1)
        caller_symbols = [c["symbol_name"] for c in result["callers"]]
        self.assertTrue(any("settleInvoiceById" in s for s in caller_symbols))


if __name__ == "__main__":
    unittest.main()
