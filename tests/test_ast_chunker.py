# tests/test_ast_chunker.py
"""
Test Suite for Slice 1: AST Code Chunker
Validates Guardrail #1 (UTF-8 multi-byte slicing) and Guardrail #2 (outer decorators & methodless types).
Compatible with both pytest and python -m unittest.
"""

import sys
from pathlib import Path
import unittest

# Ensure src is on sys.path
SRC_DIR = Path(__file__).resolve().parent.parent / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from repobrain.ast_chunker import ASTCodeChunker, compute_git_blob_sha


class TestASTChunker(unittest.TestCase):
    def test_git_blob_sha_calculation(self):
        raw_bytes = b"hello world\n"
        # Standard git sha for 'hello world\n' is sha1("blob 12\0hello world\n")
        expected = "3b18e512dba79e4c8300dd08aeb37f8e728b8dad"
        self.assertEqual(compute_git_blob_sha(raw_bytes), expected)

    def test_utf8_byte_safe_python_slicing(self):
        chunker = ASTCodeChunker()
        # Code containing multi-byte UTF-8 glyphs: € (3 bytes), ≤ (3 bytes), → (3 bytes)
        code = '''from decimal import Decimal

class CurrencyInvoice:
    """Handles EUR (€) invoices where value ≤ 50000 → approved."""
    rate: Decimal = Decimal("1.20")

@router.post("/v1/settle")
def settle_payment(amount: Decimal) -> Decimal:
    """Calculates settlement in €."""
    return amount * Decimal("1.20")
'''
        parent, children = chunker.chunk_code_string(code, virtual_path="currency.py", language="python")

        self.assertEqual(parent.language, "python")
        self.assertIn("from decimal import Decimal", parent.imports_header)
        self.assertEqual(len(children), 2)

        # Verify methodless class becomes type_definition (Guardrail #2)
        typedef_node = next(c for c in children if c.symbol_name == "CurrencyInvoice")
        self.assertEqual(typedef_node.node_kind, "type_definition")
        self.assertIn("€", typedef_node.docstring or "")
        self.assertIn("≤", typedef_node.docstring or "")
        self.assertIn("→", typedef_node.docstring or "")

        # Verify decorator preservation (Guardrail #2)
        callable_node = next(c for c in children if c.symbol_name == "settle_payment")
        self.assertEqual(callable_node.node_kind, "callable")
        self.assertIn('@router.post("/v1/settle")', callable_node.signature)
        self.assertIn('@router.post("/v1/settle")', callable_node.body_code)
        self.assertIn("€", callable_node.docstring or "")

    def test_typescript_ast_chunking(self):
        chunker = ASTCodeChunker()
        ts_code = '''import { Request, Response } from "express";

export interface SettlementRequest {
  invoiceId: string;
  totalEur: number;
}

export const processSettlement = async (req: SettlementRequest): Promise<boolean> => {
  return req.totalEur > 0;
};
'''
        parent, children = chunker.chunk_code_string(ts_code, virtual_path="settle.ts", language="typescript")

        self.assertEqual(parent.language, "typescript")
        self.assertIn('import { Request, Response }', parent.imports_header)
        self.assertEqual(len(children), 2)

        iface_node = next(c for c in children if c.symbol_name == "SettlementRequest")
        self.assertEqual(iface_node.node_kind, "type_definition")

        fn_node = next(c for c in children if c.symbol_name == "processSettlement")
        self.assertEqual(fn_node.node_kind, "callable")
        self.assertIn("processSettlement", fn_node.signature)


if __name__ == "__main__":
    unittest.main()

