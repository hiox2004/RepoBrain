# RepoBrain Master Build Plan & Autonomous Execution Engine (V2 Revised)

A Model Context Protocol (MCP)-native codebase memory, self-correcting episodic learning system, and deterministic execution harness that connects frontier coding agents (Google Antigravity IDE, Claude Code, OpenAI Codex, and local open-source models via Ollama/vLLM) to local repositories over `stdio` JSON-RPC without overflowing context windows or permitting unverified code mutations.

## User Review & Critical Decisions

> [!IMPORTANT]
> The architectural directions confirmed during Phase 1 clarification and the master specifications from `00_MASTER_BUILD_PLAN.pdf` have been synthesized into this revised blueprint:

- **Confirmed Decision 1 (Runtime Orchestration)**: An interactive in-browser agent runner with real-time JSON-RPC step execution, coupled with a full-stack Express controller proxying tool calls and streaming 5-phase CoT reasoning.
- **Confirmed Decision 2 (AI Model Backend)**: Server-side Gemini API integration via the `@google/genai` TypeScript SDK (`gemini-3.8-flash`), paired with a deterministic T=0.0 simulation replay for 100% reliable 4-Gate verification benchmarking.
- **Confirmed Decision 3 (Stream Presentation)**: A high-density, multi-panel stream layout showing synchronized AST diffs, sanitized test execution logs (stripped of `site-packages/` and `node_modules/`), and Layer 2 self-healing episodic memory updates.
- **Revision from Master PDF**: Upgraded from the 3-subsystem baseline to the full **4-Layer Architecture** (AST Codebase Memory, Self-Correcting Episodic Memory, ResearchBrain CRAG, and GitHub Template Stockroom) exposing **5 FastMCP Tools** with **Chief Lead vs. Errand Worker** model delegation.
- **Living Documentation Requirement**: The complete self-contained interactive masterclass (`04_REPOBRAIN_COMPLETE_CTO_MASTERGUIDE.html`) is permanently preserved in `/docs` and embedded directly within the workbench for continuous reference.

---

## 1. Overview & Core Concept

### 1.1 The Three Foundational LLM Failure Modes Mitigated
1. **Problem 1 — Context Bloat & "Lost in the Middle" Attention Degradation**: Ingesting 10+ raw files inflates token costs and degrades transformer attention over middle tokens, causing hallucinated code edits. RepoBrain solves this via hierarchical tree-sitter Parent-Child AST Chunking, indexing granular `ASTChildNode` units (callable, method, type_definition) while dynamically wrapping them upon retrieval in their structural `ASTParentNode` context (`imports_header`, `enclosing_scope`, `file_path`, `git_blob_sha`), cutting per-symbol context consumption from ~8,000 tokens down to 300–600 tokens.
2. **Problem 2 — Alphanumeric Blindness in Continuous Vector Spaces**: Purely dense semantic embeddings fail to distinguish exact function names, variable identifiers, and API route strings (such as confusing `getUserById` with `updateUserById`). RepoBrain solves this via a two-stage Hybrid Retrieval Pipeline: pairing pgvector HNSW cosine distance (`<=>`) with an identifier-normalized PostgreSQL `tsvector` Full-Text Search (BM25/GIN) index, fusing the top 40 dense and top 40 sparse candidates via Reciprocal Rank Fusion (RRF, $k = 60$) into a 25-candidate pool, and reranking that pool on CPU with a local Cross-Encoder (`cross-encoder/ms-marco-MiniLM-L-6-v2`) to return the final `top_k` results.
3. **Problem 3 — Non-Deterministic Self-Verification Bias**: LLMs evaluating their own generated diffs suffer from internal consistency bias and, when left unchecked in a terminal, will run failing tests 8–12 times in a row or weaken test assertions just to make them pass. RepoBrain enforces a Bounded Execution Harness that validates diffs with `git apply --check`, runs pytest/vitest inside an isolated subprocess or network-disabled, read-only Docker container (`--network=none --read-only --tmpfs /tmp:rw,exec,nosuid`), strips third-party stack frames, and enforces a hard ceiling of $\le 3$ self-healing iterations backed by non-destructive, per-file byte snapshots and surgical rollback.

### 1.2 Open-Source Ground Base Matrix
Rather than writing low-level parsers and transport layers from scratch, RepoBrain leverages battle-tested patterns from seven production open-source repositories:
- **`Consiliency/treesitter-chunker`**: Precompiled tree-sitter language bindings, AST traversal patterns, and UTF-8 byte-offset slicing.
- **`Aider-AI/aider`**: `.scm` tree-sitter query patterns (`repomap.py`) for Python/TypeScript symbols and resilient unified diff validation (`udiff_coder.py`).
- **`pavangupta352/pghybrid`**: Single-database PostgreSQL `pgvector` + `tsvector` hybrid search fused via `FULL OUTER JOIN` Reciprocal Rank Fusion ($k=60$).
- **`pgvector/pgvector-python`**: Official `register_vector` adapter for psycopg v3, HNSW index parameters ($m = 16, ef\_construction = 64$), and Cross-Encoder reranking.
- **`modelcontextprotocol/python-sdk` & `jlowin/fastmcp`**: Official `@mcp.tool()` decorators, Pydantic v2 schema serialization, `stdio` JSON-RPC server loop, and `mcp dev` inspector.
- **`SWE-agent/SWE-ReX`**: Deterministic subprocess and read-only Docker container execution with timeout enforcement and stdout/stderr capture.
- **`oraios/serena`**: Symbol-level MCP tool ergonomics and `uv` server launch configuration for Antigravity IDE and Claude Code.

---

## 2. The 4 Compounding Memory Layers & 5 FastMCP Tools

### 2.1 Layer 1: Structural Codebase Memory (Live AST State)
- **Two-Tier AST Hierarchy**: Parses Python (`tree-sitter-python`) and TypeScript (`tree-sitter-typescript`) into Concrete Syntax Trees.
- **Parent Nodes (`ASTParentNode`)**: Captures file-level structural wrappers (module, class_definition, imports_header, git_blob_sha).
- **Child Nodes (`ASTChildNode`)**: Captures searchable functional and schema units (`callable`, `method`, `type_definition`), preserving outer decorators and methodless type definitions.
- **Live Incremental SHA Sync**: Computes Git object blob SHA `sha1("blob " + len + "\0" + bytes)` on every patch or rollback, executing transactional UPSERTs (`ON CONFLICT (file_path) DO UPDATE`) with cascading child deletion.
- **MCP Tool**: `search_codebase(query: str, top_k: int = 5, include_episodes: bool = True)`

### 2.2 Layer 2: Episodic Diagnostic Memory (Self-Correcting Bug Cache)
- **Fail-to-Resolution Distillation**: Whenever the self-healing loop transitions from a failing test (`exit_code != 0` on Attempt 1 or 2) to a passing test (`exit_code == 0` on Attempt 2 or 3), RepoBrain serializes the normalized `error_signature`, `target_symbol`, a compact `root_cause_summary`, and the passing `resolution_diff` into `project_episodes`.
- **Historical Regression Prevention**: Subsequent searches inject matching episodic bug records alongside AST code blocks so the agent immediately applies proven fixes without repeating prior mistakes.

### 2.3 Layer 3: Conceptual ResearchBrain (Corrective RAG / CRAG)
- **Local Domain Knowledge Base**: Pre-indexes framework docs, RFCs, and Architecture Decision Records (`.repobrain/kb/`).
- **Deterministic Grader ($\ge 0.75$)**: Scores local confidence. If $\ge 0.75$, spends **0 external search tokens**.
- **Bounded 1-Hop Web Fallback + Extractive Compaction**: Executes at most 1 external search, strips HTML/ads, uses the local Cross-Encoder to extract the top 3 code passages (<800 tokens), verifies grounding, and auto-caches the markdown brief locally.
- **MCP Tool**: `research_technology(topic_or_query: str, domain: str = "general_tech")`

### 2.4 Layer 4: GitHub Base-Build & Template Stockroom
- **Curated Starter Blueprints**: Indexes production-vetted repositories (`tiangolo/full-stack-fastapi-template`, `shadcn-ui/taxonomy`, `astral-sh/uv`, `modelcontextprotocol/servers`, `oraios/serena`, `taskiq-python/taskiq`) in `template_blueprints`.
- **Dual Advisory Protocol**: Injects verified architecture patterns into the agent's prompt while simultaneously citing the exact repo, file path, and lines to the developer.
- **MCP Tool**: `search_templates(query: str, stack_domain: str = "all")`

### 2.5 Sub-System 3: Bounded Execution Sandbox Harness
- **Diff Pre-Validation**: Validates diffs with `git apply --check` without incrementing iteration.
- **Per-Task Byte Snapshot**: Snapshots exact pre-task file bytes before mutating disk.
- **Static Pre-Gate**: Runs fast syntax checks (`py_compile`, `ruff`, `tsc --noEmit`) before test runner invocation.
- **Surgical Rollback**: If Attempt 3 fails tests, restores only touched files to exact pre-task bytes (never `git reset --hard`) and re-indexes PostgreSQL.
- **MCP Tools**: `apply_git_patch(patch_str: str, test_path: str, task_id: str)` and `run_test_suite(test_path: str, task_id: str)`

---

## 3. The 8 Non-Negotiable Production Engineering Guardrails

1. **Guardrail #1 — UTF-8 Byte-Offset AST Slicing**: Slices raw `source_bytes[node.start_byte:node.end_byte].decode("utf-8")` so multi-byte characters (`€`, `≤`, `→`, emojis) never shift function signatures or bodies.
2. **Guardrail #2 — Outer Decorator & Methodless Type-Definition Preservation**: Unwraps `decorated_definition` / `export_statement` outer slice boundaries so route and tool decorators stay attached. Indexes zero-method classes as `node_kind="type_definition"`.
3. **Guardrail #3 — Sub-Token Identifier Normalization in PostgreSQL**: Enforces `normalize_code_identifiers()` preserving exact tokens while appending split camelCase, PascalCase, and snake_case sub-tokens into stored tsvectors.
4. **Guardrail #4 — Disjunction (|) Lexical Fallback & Length Normalization**: Replaces strict boolean AND with disjunction (`|`) tsquery over normalized tokens; scores matches with `ts_rank_cd(fts_tokens, ts_q, 32)`.
5. **Guardrail #5 — Two-Stage RRF (k = 60) -> Cross-Encoder Reranking Funnel**: Fetches Top 40 dense + Top 40 sparse candidates, fuses via FULL OUTER JOIN RRF ($k=60$) into a 25-candidate pool, reranks with `cross-encoder/ms-marco-MiniLM-L-6-v2`, and slices the final `top_k`.
6. **Guardrail #6 — Live Incremental AST Sync on Every Patch & Rollback**: Recomputes Git blob SHA and upserts modified files in PostgreSQL via `UNIQUE(file_path)` and `ON DELETE CASCADE` so Retry #2 never reads stale line numbers.
7. **Guardrail #7 — Non-Destructive Per-Task Byte Snapshots & Surgical Rollback**: Never runs `git reset --hard`. Snapshots pre-task byte contents of touched files and restores only those files if Retry #3 fails, leaving unrelated uncommitted files intact.
8. **Guardrail #8 — FastMCP stdio Hygiene, Sanctuary Policy & Sandbox Containment**: Forces all logging and progress bars to `sys.stderr` (`TOKENIZERS_PARALLELISM="false"`, `HF_HUB_DISABLE_PROGRESS_BARS="1"`), validates paths against `.repobrain/policy.toml`, rejects leading `-` flags, and runs Docker sandboxes with `--network=none --read-only --tmpfs /tmp:rw,exec,nosuid`.

---

## 4. Technical Architecture, Multi-Model Delegation & System Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          RepoBrain Web Workbench                            │
│                                                                             │
│  ┌───────────────────────┐  ┌─────────────────────┐  ┌───────────────────┐  │
│  │ 5-Phase CoT Streaming │  │ Unified Diff Viewer │  │ Test & Memory Box │  │
│  │  Reasoning & Tokens   │  │  AST Line Alignment │  │ Trace & Episodes  │  │
│  └───────────┬───────────┘  └──────────┬──────────┘  └─────────┬─────────┘  │
│              │                         │                       │            │
│              └─────────────────────────┼───────────────────────┘            │
│                                        │ Fetch / Stream Events              │
└────────────────────────────────────────┼────────────────────────────────────┘
                                         ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                   Server-Side Agent Controller (Express)                    │
│                                                                             │
│  POST /api/repobrain/prompt-loop                                            │
│    ├── Coordinates Chief Lead Model (Gemini 3.8 Flash / Claude Code)        │
│    ├── Coordinates Errand Workers (Local CPU / Fast Flash):                 │
│    │     • AST Contract Folding (>150-line functions)                       │
│    │     • Query Token Expansion & Identifier Normalization                 │
│    │     • 40-word Bug Post-Mortems for Episodic Distillation               │
│    │     • Static Type/Lint Pre-Gates in 150ms                              │
│    │     • CRAG HTML Compactor & Grounding Verifier                         │
│    ├── FastMCP Tool Dispatch:                                               │
│    │     1. search_codebase()        4. apply_git_patch()                   │
│    │     2. research_technology()    5. run_test_suite()                    │
│    │     3. search_templates()                                              │
│    └── Streams SSE events to UI: reasoning, tool_call, diff, test_result   │
└────────────────────────────────────────┬────────────────────────────────────┘
                                         ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                      Python FastMCP Execution Engine                        │
│                                                                             │
│  ┌─────────────────────────┐  ┌───────────────────────┐  ┌────────────────┐ │
│  │ Layer 1: AST Chunker    │  │ Layer 2: Episodic DB  │  │ Layer 3: CRAG  │ │
│  │ • UTF-8 byte slicer     │  │ • Fail->Pass distill  │  │ • Local RFC KB │ │
│  │ • Parent-Child split    │  │ • Error signatures    │  │ • 1-hop web    │ │
│  │ • Decorator preservation│  │ • Regression shield   │  │ • Compactor    │ │
│  └─────────────────────────┘  └───────────────────────┘  └────────────────┘ │
│  ┌─────────────────────────┐  ┌───────────────────────┐  ┌────────────────┐ │
│  │ Layer 4: Template Stock │  │ Hybrid Retriever      │  │ Bounded Harness│ │
│  │ • tiangolo/fastapi      │  │ • pgvector HNSW       │  │ • git check    │ │
│  │ • shadcn/taxonomy       │  │ • BM25 GIN tsvector   │  │ • Byte snapshot│ │
│  │ • dual advisory cite    │  │ • RRF (k=60) + CE     │  │ • Surgical undo│ │
│  └─────────────────────────┘  └───────────────────────┘  └────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 5. Stepwise Implementation & Rollout Plan

### Step 1: Target Repository Directory Structure
Ensure all directories, schemas, and configurations are maintained in the repository:
```
repobrain/
├── pyproject.toml
├── docker-compose.yml
├── Dockerfile.sandbox
├── mcp_config.json
├── docs/
│   └── 04_REPOBRAIN_COMPLETE_CTO_MASTERGUIDE.html   # Living interactive masterclass
├── sql/
│   ├── 02_DATABASE_SCHEMA_AND_RRF.sql
│   └── 03_EPISODIC_RESEARCH_AND_TEMPLATES_SCHEMA.sql
├── src/
│   ├── repobrain/
│   │   ├── __init__.py
│   │   ├── schemas.py
│   │   ├── ast_chunker.py
│   │   ├── hybrid_retriever.py
│   │   ├── server.py
│   │   ├── episodic_memory.py
│   │   ├── research_brain.py
│   │   ├── template_stockroom.py
│   │   └── pre_sandbox_guards.py
│   └── billing/
│       └── ledger.py                                 # Reference test fixture
└── tests/
    ├── fixtures/
    ├── test_ast_chunker.py
    ├── test_rrf_retrieval.py
    └── test_bounded_harness.py
```

### Step 2: Living HTML Masterguide Integration
- Keep `docs/04_REPOBRAIN_COMPLETE_CTO_MASTERGUIDE.html` version-controlled in the repository.
- Expose an in-app **"CTO Masterguide"** tab inside the React workbench that renders this complete interactive guide (with its reading depth filter, interactive UTF-8 simulator, identifier splitter, RRF calculator, and 8-question self-test) so developers can study the architecture directly while running the system.

### Step 3: Interactive Prompt Loop Engine in Web Workbench
- Integrate the live 5-phase CoT runner into the React frontend.
- Allow users to trigger real-time prompt runs (e.g. against `src/billing/ledger.py`), view the streaming XML reasoning tags, watch the minimal unified diffs render in real-time, inspect the stripped tracebacks, and witness the automatic episodic memory distillation into `project_episodes`.
- Include 1-click execution for the 4-Gate Deterministic Verification Stress Test to verify Guardrails 1 through 8.
