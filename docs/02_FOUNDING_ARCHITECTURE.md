# RepoBrain V2 & ResearchBrain OS: Founding Architecture Blueprint
**Status:** Unified System Specification (T = 0.0 Deterministic)  
**Target Environment:** VS Code + Google Antigravity Agent (`stdio` FastMCP, Background Task Manager, Unified Diff / AST Artifacts)  

---

## 1. System Topology & Core Architectural Invariants

RepoBrain V2 is an autonomous codebase memory engine, semantic retrieval pipeline, and deterministic execution harness operating over standard Model Context Protocol (MCP) JSON-RPC. It mitigates the three primary LLM failure modes:
1. **Context Bloat & Attention Degradation:** Solved via parent-child AST slicing (sub-symbol retrieval wrapped in file-level import headers, cutting context by ~90%).
2. **Alphanumeric & Identifier Blindness:** Solved via Two-Stage Hybrid RRF ($k=60$) fusing pgvector HNSW cosine similarity with identifier-normalized PostgreSQL tsvectors (GIN), reranked on CPU via Cross-Encoder.
3. **Runaway Verification Bias:** Solved via a bounded $\le 3$-iteration harness enforcing diff pre-validation (`git apply --check`), static syntax pre-gates (`py_compile`/`ruff`/`tsc`), and non-destructive surgical byte snapshot rollback.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          VS Code + Antigravity IDE                          │
│                                                                             │
│  ┌───────────────────────┐  ┌─────────────────────┐  ┌───────────────────┐  │
│  │ 5-Phase CoT Streaming │  │ Unified Diff Viewer │  │ Test & Memory Box │  │
│  │ <thought>/<action>... │  │  AST Line Alignment │  │ Traces & Episodes │  │
│  └───────────┬───────────┘  └──────────┬──────────┘  └─────────┬─────────┘  │
│              │                         │                       │            │
│              └─────────────────────────┼───────────────────────┘            │
│                                        │ stdio JSON-RPC                     │
└────────────────────────────────────────┼────────────────────────────────────┘
                                         ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                       RepoBrain V2 FastMCP Server                           │
│  sys.stderr Logging | TOKENIZERS_PARALLELISM=false | HF Progress Disabled   │
│                                                                             │
│  ┌─────────────────────────────────┐   ┌─────────────────────────────────┐  │
│  │ Layer 1: Structural AST Memory  │   │ Layer 2: Episodic Memory        │  │
│  │ • ast_chunker.py (Tree-sitter)  │   │ • episodic_memory.py            │  │
│  │ • UTF-8 byte boundary slicing   │   │ • Fail->Pass diagnostic cache   │  │
│  │ • Decorator & type preservation │   │ • Regression immunization       │  │
│  └─────────────────────────────────┘   └─────────────────────────────────┘  │
│  ┌─────────────────────────────────┐   ┌─────────────────────────────────┐  │
│  │ Layer 3: Conceptual Research    │   │ Layer 4: Template Stockroom     │  │
│  │ • research_brain.py (CRAG)      │   │ • template_stockroom.py         │  │
│  │ • Local ADRs/RFCs (>=0.75 conf) │   │ • Vetted scaffolding blueprints │  │
│  │ • Bounded 1-hop web compactor   │   │ • Dual advisory citation model  │  │
│  └─────────────────────────────────┘   └─────────────────────────────────┘  │
│  ┌─────────────────────────────────┐   ┌─────────────────────────────────┐  │
│  │ Hybrid RRF Retriever            │   │ Bounded Execution Harness       │  │
│  │ • hybrid_retriever.py           │   │ • pre_sandbox_guards.py         │  │
│  │ • pgvector HNSW + GIN tsvector  │   │ • server.py                     │  │
│  │ • Cross-Encoder CPU Rerank      │   │ • <= 3 retries + byte rollback  │  │
│  └─────────────────────────────────┘   └─────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. The 5 Core Pillars & Mathematical Foundations

### Pillar 1: Layer 1 — Structural Codebase Memory (`search_codebase`)
- **Parent-Child Contract:** Code is decomposed into `ASTParentNode` (file envelope, module-level import headers, enclosing scope, and Git blob SHA) and searchable `ASTChildNode` entities (`callable`, `method`, `type_definition`).
- **UTF-8 Byte Boundary Invariant:** Slices are generated using raw UTF-8 byte offsets `source_bytes[node.start_byte:node.end_byte].decode("utf-8")`. Character-based string slicing on multi-byte characters (`€` = 3 bytes, `≤` = 3 bytes, `→` = 3 bytes, emojis = 4 bytes) is strictly forbidden.
- **Outer Decorators & Methodless Schemas:** Decorators (`@mcp.tool()`, `@router.post()`, `@dataclass`) are annexed to the child definition. Methodless classes (Pydantic `BaseModel`, TypeScript `interface`/`type`) are indexed with `node_kind="type_definition"`.
- **Hybrid Reciprocal Rank Fusion ($k=60$):**
  $$\text{RRF Score}(c) = \frac{1}{60 + \text{Rank}_{\text{dense}}(c)} + \frac{1}{60 + \text{Rank}_{\text{sparse}}(c)}$$
  Top 40 dense vector candidates ($\vec{v}_{\text{query}} \Leftrightarrow \vec{v}_{\text{child}}$) and Top 40 sparse candidates (`ts_rank_cd(fts_tokens, ts_q, 32)`) are merged via FULL OUTER JOIN into a 25-candidate pool, then reranked by Cross-Encoder (`ms-marco-MiniLM-L-6-v2`) on CPU.

### Pillar 2: Layer 2 — Self-Correcting Episodic Diagnostic Memory (`project_episodes`)
- **Fail-to-Pass Distillation:** When a task transitions from a test failure (`exit_code != 0` on Attempt 1 or 2) to a test pass (`exit_code == 0` on Attempt 2 or 3), an Errand Worker distills:
  1. `error_signature`: Cleaned exception line (e.g. `AssertionError: Decimal('120.0000') != Decimal('120.00')`).
  2. `target_symbol`: e.g. `LedgerService.settleInvoiceById`.
  3. `root_cause_summary`: $\le 40$-word explanation.
  4. `resolution_diff`: Verified minimal unified diff.
- **Immunization:** Subsequent queries automatically retrieve matching episodes and prepend `<past_episodic_fix>` blocks before the agent touches code.

### Pillar 3: Layer 3 — Conceptual ResearchBrain (`research_technology`)
- **5-Phase Bounded Corrective RAG (CRAG):**
  1. *Semantic Router:* Short-circuits known parametric queries.
  2. *Local Domain Tech KB:* Searches `.repobrain/kb/` (ADRs, RFCs, local framework documentation) via Hybrid RRF.
  3. *Retrieval Grader:* Scores local relevance. If score $\ge 0.75$, responds immediately at **0 external token cost**. If $< 0.75$, triggers at most **1 bounded web search**.
  4. *Extractive Passage Compactor:* Strips HTML, headers, navbars, and advertisements, isolating 3 dense snippets totaling $< 1,000$ tokens.
  5. *Grounding Check & Markdown Cache:* Verifies citations and caches markdown briefs in `.repobrain/kb_cache/<slug>.md`.

### Pillar 4: Layer 4 — GitHub Template Stockroom (`search_templates`)
- **Vetted Blueprints:** Maintains curated blueprints (`tiangolo/full-stack-fastapi-template`, `shadcn-ui/taxonomy`, `astral-sh/uv`, `oraios/serena`, `taskiq-python/taskiq`).
- **Dual Advisory Protocol:** Simultaneously advises the agent with idiomatic patterns and instructs the agent to cite source repo and line ranges to the developer.

### Pillar 5: Bounded Execution Sandbox & Errand Worker Gates
- **Sanctuary Policy Guard:** Rejects file modifications targeting protected globs (`*.lock`, `.env`, `.repobrain/policy.toml`) or traversing directories (`../`).
- **Surgical Byte Snapshot Rollback:** Snapshots exact pre-task raw bytes in memory. If Retry #3 fails, it restores only the snapshotted files. It **never** executes `git reset --hard`, keeping uncommitted developer work completely safe.
- **stdio Hygiene:** Standard output is reserved strictly for JSON-RPC messages. All diagnostic logs, model loading notifications, and stack traces stream to `sys.stderr`.

---

## 3. The 8 Production Engineering Guardrails

1. **Guardrail #1:** UTF-8 Byte-Offset AST Slicing (zero line/column drift on multi-byte characters).
2. **Guardrail #2:** Outer Decorator & Methodless Type Definition Preservation.
3. **Guardrail #3:** Split-Token Identifier Normalization (`camelCase` / `snake_case` expanded in PostgreSQL `tsvector`).
4. **Guardrail #4:** Disjunction (`|`) Lexical Fallback & Length Normalization (`ts_rank_cd(..., 32)`).
5. **Guardrail #5:** Two-Stage RRF ($k=60$) & CPU Cross-Encoder Reranking Funnel.
6. **Guardrail #6:** Live Incremental Git Blob SHA Index Sync on every patch and rollback.
7. **Guardrail #7:** Non-Destructive Per-Task Byte Snapshots & Surgical Rollback (no `git reset --hard`).
8. **Guardrail #8:** stdio Hygiene (`sys.stderr` only), Sanctuary Policy Guard, and sanitized test runner execution.

