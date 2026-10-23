# tests/test_typescript_nextjs.py
"""
Unit and integration tests for TypeScript, Next.js 15, and static syntax pre-gates.
Tests AST chunking of Server Actions, App Router pages, Zod schemas, and syntax validation.
"""

import shutil
import sys
import unittest
from pathlib import Path

SRC_DIR = Path(__file__).resolve().parent.parent / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from repobrain.ast_chunker import ASTCodeChunker
from repobrain.pre_sandbox_guards import fast_static_syntax_check


class TestTypeScriptNextJS(unittest.TestCase):
    def setUp(self):
        self.chunker = ASTCodeChunker()
        self.test_dir = Path("test_scratch_ts")
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)
        self.test_dir.mkdir(parents=True, exist_ok=True)

    def tearDown(self):
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)

    def test_chunk_nextjs15_server_action_and_zod(self):
        """Verify extraction of 'use server' directive, Zod schemas, and Server Actions."""
        ts_code = '''"use server";

import { z } from 'zod';
import { db } from '@/lib/db';

export const InvoiceSchema = z.object({
  invoiceId: z.string(),
  amount: z.number().positive(),
});

export type InvoiceInput = z.infer<typeof InvoiceSchema>;

export async function settleInvoiceAction(data: InvoiceInput) {
  const parsed = InvoiceSchema.parse(data);
  return await db.invoices.update({ where: { id: parsed.invoiceId }, data: { status: 'PAID' } });
}
'''
        parent, children = self.chunker.chunk_code_string(
            ts_code, virtual_path="app/actions/invoices.ts", language="typescript"
        )

        self.assertIn('"use server";', parent.imports_header)
        self.assertEqual(parent.enclosing_scope, "directive:use server")

        symbol_names = [c.symbol_name for c in children]
        self.assertIn("InvoiceSchema", symbol_names)
        self.assertIn("InvoiceInput", symbol_names)
        self.assertIn("ServerAction.settleInvoiceAction", symbol_names)

        # Check node kinds
        schema_node = next(c for c in children if c.symbol_name == "InvoiceSchema")
        self.assertEqual(schema_node.node_kind, "type_definition")

        action_node = next(c for c in children if c.symbol_name == "ServerAction.settleInvoiceAction")
        self.assertEqual(action_node.node_kind, "callable")
        self.assertIn("InvoiceSchema.parse", action_node.body_code)

    def test_chunk_nextjs_app_router_page(self):
        """Verify extraction of Next.js App Router async default export page."""
        tsx_code = '''import React from 'react';
import { Header } from '@/components/Header';

export default async function InvoiceDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  return (
    <main className="p-8">
      <h1>Invoice #{id}</h1>
    </main>
  );
}
'''
        parent, children = self.chunker.chunk_code_string(
            tsx_code, virtual_path="app/invoices/[id]/page.tsx", language="typescript"
        )

        self.assertEqual(len(children), 1)
        page_node = children[0]
        self.assertEqual(page_node.symbol_name, "InvoiceDetailPage")
        self.assertEqual(page_node.node_kind, "callable")
        self.assertIn("await params", page_node.body_code)

    def test_chunk_typescript_class_methods(self):
        """Verify extraction of TypeScript class and individual class methods."""
        ts_code = '''export class LedgerService {
  constructor(private taxRate: number = 0.20) {}

  public async settleInvoice(invoiceId: string, subtotal: number): Promise<number> {
    return subtotal * (1.0 + this.taxRate);
  }

  public getTaxRate(): number {
    return this.taxRate;
  }
}
'''
        parent, children = self.chunker.chunk_code_string(
            ts_code, virtual_path="src/services/ledger.ts", language="typescript"
        )

        symbols = [c.symbol_name for c in children]
        self.assertIn("LedgerService.settleInvoice", symbols)
        self.assertIn("LedgerService.getTaxRate", symbols)

        method_node = next(c for c in children if c.symbol_name == "LedgerService.settleInvoice")
        self.assertEqual(method_node.node_kind, "method")

    def test_typescript_static_syntax_pre_gate(self):
        """Verify that pre_sandbox_guards catches unclosed delimiters before running tests."""
        bad_file = self.test_dir / "broken.ts"
        bad_file.write_text("export function badFunction() { return 42;\n", encoding="utf-8")

        passed, err = fast_static_syntax_check(self.test_dir, ["broken.ts"])
        self.assertFalse(passed, "Pre-gate must fail on unclosed brace.")
        self.assertIn("Unclosed delimiter '{'", err)

        good_file = self.test_dir / "clean.ts"
        good_file.write_text("export function cleanFunction() { return 42; }\n", encoding="utf-8")
        good_passed, good_err = fast_static_syntax_check(self.test_dir, ["clean.ts"])
        self.assertTrue(good_passed, "Pre-gate must pass on clean TS syntax.")
        self.assertEqual(good_err, "")


if __name__ == "__main__":
    unittest.main()

