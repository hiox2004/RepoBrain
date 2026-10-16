// src/data/repobrainData.ts
import { ASTParentNode, ASTChildNode, EpisodicFixRecord, PatchAndTestResponse } from '../types/repobrain';

export const SAMPLE_LEDGER_CODE = `# src/billing/ledger.py
from decimal import Decimal
from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()

class InvoiceRequest(BaseModel):
    """Schema for incoming EUR (€) invoices where amount ≤ 10000 → auto-settled."""
    invoice_id: str
    subtotal: Decimal

class LedgerService:
    def __init__(self, tax_rate: Decimal = Decimal("0.20")) -> None:
        self.tax_rate = tax_rate

    @router.post("/v1/invoices/settle")
    async def settleInvoiceById(self, req: InvoiceRequest) -> Decimal:
        """Calculates total gross amount (subtotal → gross) in €."""
        # BUG: subtracts tax_rate instead of adding, and omits .quantize(Decimal("0.01"))
        return req.subtotal * (Decimal("1.00") - self.tax_rate)`;

export const GATE1_PARENT_NODE: ASTParentNode = {
  parent_id: "49433734-7ff4-4316-a549-095c1715ebd7",
  file_path: "src/billing/ledger.py",
  language: "python",
  imports_header: "from decimal import Decimal\nfrom fastapi import APIRouter\nfrom pydantic import BaseModel",
  enclosing_scope: null,
  git_blob_sha: "084638d16cca45ce180c307abd51468bf2f423c9"
};

export const GATE1_CHILD_NODES: ASTChildNode[] = [
  {
    child_id: "9d6e0b6b-1ea2-42f1-91de-8ef84fd5b0bd",
    parent_id: "49433734-7ff4-4316-a549-095c1715ebd7",
    file_path: "src/billing/ledger.py",
    node_kind: "type_definition",
    symbol_name: "InvoiceRequest",
    signature: "class InvoiceRequest(BaseModel):",
    docstring: "Schema for incoming EUR (€) invoices where amount ≤ 10000 → auto-settled.",
    body_code: `class InvoiceRequest(BaseModel):
    """Schema for incoming EUR (€) invoices where amount ≤ 10000 → auto-settled."""
    invoice_id: str
    subtotal: Decimal`,
    start_line: 8,
    end_line: 11
  },
  {
    child_id: "ed94eb26-9850-40e0-b6e7-18a355d0bc1d",
    parent_id: "49433734-7ff4-4316-a549-095c1715ebd7",
    file_path: "src/billing/ledger.py",
    node_kind: "method",
    symbol_name: "LedgerService.__init__",
    signature: 'def __init__(self, tax_rate: Decimal = Decimal("0.20")) -> None:',
    docstring: null,
    body_code: `    def __init__(self, tax_rate: Decimal = Decimal("0.20")) -> None:
        self.tax_rate = tax_rate`,
    start_line: 14,
    end_line: 15
  },
  {
    child_id: "b6593342-1d29-45ea-827d-677f564d09b0",
    parent_id: "49433734-7ff4-4316-a549-095c1715ebd7",
    file_path: "src/billing/ledger.py",
    node_kind: "method",
    symbol_name: "LedgerService.settleInvoiceById",
    signature: `@router.post("/v1/invoices/settle")
async def settleInvoiceById(self, req: InvoiceRequest) -> Decimal:`,
    docstring: "Calculates total gross amount (subtotal → gross) in €.",
    body_code: `    @router.post("/v1/invoices/settle")
    async def settleInvoiceById(self, req: InvoiceRequest) -> Decimal:
        """Calculates total gross amount (subtotal → gross) in €."""
        # BUG: subtracts tax_rate instead of adding, and omits .quantize(Decimal("0.01"))
        return req.subtotal * (Decimal("1.00") - self.tax_rate)`,
    start_line: 17,
    end_line: 21
  }
];

export const GATE2_PROOF = {
  query: "settleInvoiceById decimal quantization",
  normalizedIdentifier: "settleInvoiceById settle invoice by id",
  disjunctionTsquery: "'settleInvoiceById' | 'decimal' | 'quantization' | 'settle' | 'invoice' | 'by' | 'id'",
  tokens: ["settleInvoiceById", "decimal", "quantization", "settle", "invoice", "by", "id"],
  candidates: [
    {
      symbol: "Node A (settleInvoiceById)",
      denseRank: 3,
      sparseRank: 1,
      denseCalc: "1 / (60 + 3) = 1/63 ≈ 0.01587302",
      sparseCalc: "1 / (60 + 1) = 1/61 ≈ 0.01639344",
      rrfScore: 0.032266,
      rerankScore: 0.9420,
      note: "Exact lexical hit on normalized sub-tokens + high dense similarity. Top candidate."
    },
    {
      symbol: "Node B (calculate_tax_summary)",
      denseRank: 1,
      sparseRank: 12,
      denseCalc: "1 / (60 + 1) = 1/61 ≈ 0.01639344",
      sparseCalc: "1 / (60 + 12) = 1/72 ≈ 0.01388889",
      rrfScore: 0.030282,
      rerankScore: 0.6120,
      note: "Top dense semantic match, but lower lexical presence for settleInvoiceById."
    },
    {
      symbol: "Node C (InvoiceRequest)",
      denseRank: 2,
      sparseRank: null,
      denseCalc: "1 / (60 + 2) = 1/62 ≈ 0.01612903",
      sparseCalc: "0.00000000 (lexically unmatched)",
      rrfScore: 0.016129,
      rerankScore: 0.4510,
      note: "Pydantic data contract indexed via Guardrail #2; partial dense semantic relevance."
    }
  ],
  xmlBlock: `<ast_context file="src/billing/ledger.py" symbol="LedgerService.settleInvoiceById" kind="method" lines="17-21" sha="084638d16cca45ce180c307abd51468bf2f423c9" rrf="0.032266" rerank="0.9420">
  <parent_imports>
from decimal import Decimal
from fastapi import APIRouter
from pydantic import BaseModel
  </parent_imports>
  <enclosing_scope>
class LedgerService
  </enclosing_scope>
  <child_body>
    @router.post("/v1/invoices/settle")
    async def settleInvoiceById(self, req: InvoiceRequest) -> Decimal:
        """Calculates total gross amount (subtotal → gross) in €."""
        # BUG: subtracts tax_rate instead of adding, and omits .quantize(Decimal("0.01"))
        return req.subtotal * (Decimal("1.00") - self.tax_rate)
  </child_body>
</ast_context>`
};

export const GATE3_EPISODE: EpisodicFixRecord = {
  episode_id: "729371fc-6612-4532-b0e6-50d219258821",
  error_signature: "AssertionError: Decimal('120.0000') != Decimal('120.00')",
  target_symbol: "LedgerService.settleInvoiceById",
  file_path: "src/billing/ledger.py",
  root_cause_summary: "Decimal arithmetic without explicit quantization preserves full multiplicand scale; requires .quantize(Decimal('0.01')) for currency settlements.",
  resolution_diff: `--- a/src/billing/ledger.py
+++ b/src/billing/ledger.py
@@ -21,1 +21,1 @@
-        return req.subtotal * (Decimal("1.00") - self.tax_rate)
+        return (req.subtotal * (Decimal("1.00") + self.tax_rate)).quantize(Decimal("0.01"))`,
  created_at: "2026-10-15T10:48:00Z"
};

export const GATE4_ROLLBACK_RESPONSE: PatchAndTestResponse = {
  task_id: "broken-migration",
  iteration: 3,
  patch_applied: true,
  static_check_passed: true,
  tests_passed: false,
  exit_code: 1,
  rolled_back: true,
  filtered_traceback: "MigrationError: Table 'schema_migrations' locked by dead process\nAssertionError: Migration check failed",
  reindexed_files: ["src/billing/ledger.py"],
  recorded_episode_id: null
};

export const GUARDRAILS_SPEC = [
  {
    id: 1,
    title: "UTF-8 Byte-Offset AST Slicing",
    desc: "Uses raw source_bytes[node.start_byte:node.end_byte].decode('utf-8') so multi-byte UTF-8 symbols (€, ≤, →, emojis) never shift indices or truncate AST bodies.",
    badge: "Byte Slicer"
  },
  {
    id: 2,
    title: "Outer Decorator & Methodless Type-Def",
    desc: "Unwraps decorated_definition / export_statement so decorators (@mcp.tool(), @router.post(...)) remain attached; indexes methodless BaseModel / interfaces as type_definition.",
    badge: "AST Scope"
  },
  {
    id: 3,
    title: "Sub-Token Identifier Normalization",
    desc: "IMMUTABLE PARALLEL SAFE SQL function normalize_code_identifiers() preserves exact identifier while appending split camelCase, PascalCase, and snake_case sub-tokens.",
    badge: "SQL Regex"
  },
  {
    id: 4,
    title: "Disjunction (|) Lexical Fallback & Length Norm",
    desc: "Replaces strict boolean AND with disjunction (|) tsquery over normalized tokens; scores matches with ts_rank_cd(fts_tokens, ts_q, 32) so stopwords never collapse recall.",
    badge: "BM25 / FTS"
  },
  {
    id: 5,
    title: "Two-Stage RRF (k=60) -> Cross-Encoder Funnel",
    desc: "Fetches Top 40 dense + Top 40 sparse candidates, fuses via FULL OUTER JOIN RRF (k=60) into 25-candidate pool, and reranks with cross-encoder/ms-marco-MiniLM-L-6-v2.",
    badge: "Hybrid RRF"
  },
  {
    id: 6,
    title: "Live Incremental AST Sync on Patch & Rollback",
    desc: "Computes git blob SHA on every patch application and rollback, upserting in PostgreSQL via UNIQUE(file_path) with ON DELETE CASCADE so retry #2 never reads stale lines.",
    badge: "Live SHA Sync"
  },
  {
    id: 7,
    title: "Non-Destructive Byte Snapshots & Surgical Rollback",
    desc: "Never executes git reset --hard. Snapshots exact pre-task file byte contents and restores only touched files on iteration 3 failure, preserving developer uncommitted files.",
    badge: "Surgical Undo"
  },
  {
    id: 8,
    title: "FastMCP stdio Hygiene & Sandbox Containment",
    desc: "Forces all logs and tqdm bars to sys.stderr (TOKENIZERS_PARALLELISM='false') so stdout has pure JSON-RPC 2.0; blocks sanctuary files, rejects leading - flags, isolates runner.",
    badge: "Stdio Hygiene"
  }
];
