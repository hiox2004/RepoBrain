# Multi-Agent System of Working & Autonomous Orchestration Spec

**RepoBrain V2 & ResearchBrain OS**  
*Governed by Modern Autonomous Multi-Agent Practices: Role Specialization, State-Driven Transitions, Bounded Retries, and Self-Healing Loops.*

---

## 1. Multi-Agent Architecture & Role Topology

Rather than relying on a single monolithic prompt, RepoBrain orchestrates specialized, narrow-scope agents with explicit input/output data contracts:

```
                             ┌───────────────────────────────┐
                             │       User / Task Goal        │
                             └───────────────┬───────────────┘
                                             │
                                             ▼
                             ┌───────────────────────────────┐
                             │   CHIEF ARCHITECT AGENT       │
                             │  • Goal decomposition         │
                             │  • 5-Phase CoT state machine  │
                             │  • Final verdict & summary    │
                             └───────┬───────┬───────┬───────┘
                                     │       │       │
          ┌──────────────────────────┘       │       └─────────────────────────┐
          ▼                                  ▼                                 ▼
┌──────────────────┐               ┌──────────────────┐               ┌──────────────────┐
│  CODE MEMORY     │               │  RESEARCH & CRAG │               │  SENTRY & TEST   │
│  SPECIALIST      │               │  SPECIALIST      │               │  SPECIALIST      │
│  (Layer 1 & 4)   │               │  (Layer 3)       │               │  (Layer 2 & 5)   │
├──────────────────┤               ├──────────────────┤               ├──────────────────┤
│ • AST parsing    │               │ • Local ADRs/RFCs│               │ • Sanctuary guard│
│ • RRF k=60 search│               │ • Confidence >=75│               │ • Syntax checks  │
│ • SHA tracking   │               │ • 1-hop web comp.│               │ • Test runner    │
│ • Blueprint stock│               │ • Markdown cache │               │ • Distillation   │
│ • Context blocks │               │ • Grounding check│               │ • Byte rollback  │
└──────────────────┘               └──────────────────┘               └──────────────────┘
```

---

## 2. Specialized Agent Contracts

### Agent 1: Chief Architect (Orchestrator)
- **Role:** High-level coordinator, hypothesis generator, and patch synthesizer.
- **Input:** Task prompt (e.g. *"Fix decimal quantization in LedgerService.settleInvoiceById"*).
- **Duties:**
  1. Calls **Code Memory Specialist** to retrieve AST context and matching past episodes.
  2. If technical or domain concepts are uncertain, delegates to **Research & CRAG Specialist**.
  3. Formulates a $\le 40$-word diagnostic hypothesis.
  4. Synthesizes a unified diff adhering to Guardrail #1 (UTF-8 byte safety) and Guardrail #2 (decorator preservation).
  5. Delegates execution to **Sentry & Test Specialist**.
  6. Evaluates the test result: if failed and `iteration < 3`, loops back to step 3; if `iteration == 3`, confirms surgical rollback.

### Agent 2: Code Memory & Template Specialist (Layer 1 & 4)
- **Role:** Structural repository navigation and starter pattern retrieval.
- **Tools:** `search_codebase`, `search_templates`, `sync_file_if_changed`.
- **Output:** Emits clean `<ast_context>` XML blocks (parent imports + child body + past episodic fixes), ensuring token consumption remains $<600$ tokens per symbol.

### Agent 3: ResearchBrain CRAG Specialist (Layer 3)
- **Role:** Conceptual grounding, architecture decision retrieval, and bounded web synthesis.
- **Engine Architecture:** Evaluator-driven **LangGraph `StateGraph`** encapsulated strictly within `src/repobrain/research_brain.py`.
- **Tools:** `research_technology`.
- **State Schema (`CRAGState`):**
  - `query: str` & `domain: str`
  - `local_chunks: List[TechKnowledgeChunk]`
  - `confidence_score: float` (0.0 to 1.0)
  - `grade_verdict: Literal["CORRECT", "AMBIGUOUS", "INCORRECT"]`
  - `web_passages: List[str]` (< 1,000 tokens dense snippets)
  - `brief: Optional[ResearchBrief]`
- **LangGraph Node Topology & Conditional Routing:**
  1. `check_cache_node`: Checks `.repobrain/kb_cache/<slug>.md`. On hit, short-circuits to END (0 tokens, < 5ms).
  2. `retrieve_local_kb_node`: Indexes and queries `.repobrain/kb/` markdown ADRs/RFCs.
  3. `grade_retrieval_node`: Evaluates semantic relevance and computes confidence score.
  4. *Conditional Edge:*
     - If `confidence_score >= 0.75` (`CORRECT`): Route directly to `synthesize_and_cache_node` (**0 external tokens spent**).
     - If `confidence_score < 0.75` (`AMBIGUOUS`/`INCORRECT`): Route to `bounded_web_compactor_node`.
  5. `bounded_web_compactor_node`: Executes strictly **1 bounded external search hop**, strips DOM/boilerplate/navbars, and compacts to top 3 dense snippets.
  6. `synthesize_and_cache_node`: Verifies grounding, writes markdown to `.repobrain/kb_cache/<slug>.md`, and returns typed `ResearchBrief`.
- **Output:** Emits a structured `ResearchBrief` adhering to the Pydantic data contract.



### Agent 4: Sentry & Test Execution Specialist (Layer 2 & 5)
- **Role:** Execution containment, static validation, test execution, and rollback.
- **Tools:** `apply_git_patch`, `run_test_suite`.
- **Invariants:**
  - Enforces `SanctuaryPolicyGuard` (blocks `.env`, `*.lock`, `../`, and test assertion weakening at `iteration = 0`).
  - Snapshots raw file bytes before disk mutation.
  - Runs fast 150ms static syntax pre-gate (`py_compile`).
  - Executes test suite with sanitized `--` flags.
  - Strips third-party frames (`site-packages/`, `node_modules/`).
  - On fail-to-pass transitions, distills normalized post-mortem into `project_episodes`.
  - On Attempt 3 failure, executes surgical byte rollback restoring exact pre-task bytes.

---

## 3. The Autonomous Self-Correction Loop

```mermaid
stateDiagram-v2
    [*] --> ContextRetrieval
    ContextRetrieval --> HypothesisFormation: AST Context + Past Episodes
    HypothesisFormation --> SurgicalPatching: <= 40-word Root Cause
    SurgicalPatching --> PreGateValidation: Unified Diff
    PreGateValidation --> TestExecution: Syntax & Sanctuary OK
    PreGateValidation --> SurgicalPatching: Syntax Error / Sanctuary Violation

    state TestExecution {
        [*] --> RunSuite
        RunSuite --> Pass: exit_code == 0
        RunSuite --> Fail: exit_code != 0
    }

    Pass --> EpisodicDistillation: If iteration > 1 (Fail -> Pass)
    Pass --> Completed: If iteration == 1
    EpisodicDistillation --> Completed

    Fail --> SurgicalPatching: iteration < 3 (Refine Patch)
    Fail --> SurgicalRollback: iteration == 3 (Ceiling Reached)
    SurgicalRollback --> TerminatedWithRollback
    Completed --> [*]
    TerminatedWithRollback --> [*]
```

---

## 4. Multi-Agent Communication Protocol

Agents communicate over structured JSON payloads conforming to `schemas.py`. All events are recorded in an execution event trace:

```json
{
  "trace_id": "trace-uuid4",
  "task_id": "fix-settle-invoice",
  "step": 1,
  "agent": "ChiefArchitect",
  "action": "delegate_retrieval",
  "payload": {
    "query": "settleInvoiceById decimal quantization"
  },
  "timestamp": "2026-10-20T17:20:00Z"
}
```

This guarantees full determinism, observability, and auditability at every stage.

---

## 5. The Compounding Self-Learning Loop & Antigravity Native Integration

RepoBrain does not remain static; it functions as a living memory organism that compounds expertise with every development session.

```mermaid
flowchart TD
    TaskPass["Passing Task Execution (Attempt 1, 2, or 3)"] --> Micro["Tier 1: Micro-Distillation<br/>(error_signature, symbol, minimal_diff)"]
    Micro --> Cache["Append to project_episodes"]
    
    Cache --> Cluster{"Pattern Clustering<br/>Has same root cause occurred &ge; 3 times?"}
    Cluster -->|Yes| ADR["Tier 2: Macro ADR Promotion<br/>Synthesize Architectural Decision Record into .repobrain/kb/adrs/"]
    Cluster -->|No| NextQuery["Immunize Future Queries<br/>Prepend &lt;past_episodic_fix&gt; context"]
    
    ADR --> L3Index["Layer 3 CRAG Indexes New ADR<br/>Elevated to Permanent Architectural Law"]
    
    TaskPass --> PatternCheck{"Is this a clean, verified architectural pattern?<br/>(Server Action, FastAPI Dependency, LangGraph Reducer)"}
    PatternCheck -->|Yes| Harvest["Tier 3: Blueprint Harvesting<br/>Extract minimal structure into Layer 4 template_stockroom.py"]
```

### 5.1 Multi-Stack Specialization
1. **Python / FastAPI Stack:**
   - Detects Pydantic v1 vs v2 patterns (`model_validate`, `field_validator`).
   - Slices async route handlers, dependency injectors, and lifespan context managers.
   - Enforces `py_compile` syntax pre-gate and runs `pytest` with sanitized flags.
2. **TypeScript / Next.js / Node Stack:**
   - Slices React 19 / Next.js App Router Server Components, Server Actions (`"use server"`), and Zod schemas.
   - Enforces `tsc --noEmit` / fast AST static pre-gate.
   - Executes `vitest`, `jest`, or `npm test` with isolated subprocess boundaries.
3. **Agentic AI & RAG Ecosystem (LangGraph / LangChain):**
   - Indexes and validates LangGraph `StateGraph`, typed dictionaries, conditional edges, and checkpoint savers.
   - Automatically harvests reusable state graph patterns and tool node definitions into Layer 4.

### 5.2 Antigravity Native Integration
RepoBrain connects natively to **Google Antigravity** as a standard `stdio` Model Context Protocol (MCP) server.

In Antigravity's MCP configuration (`mcp_config.json` / workspace settings):
```json
{
  "mcpServers": {
    "repobrain": {
      "command": "python",
      "args": ["-m", "repobrain.server"],
      "env": {
        "PYTHONPATH": "src",
        "TOKENIZERS_PARALLELISM": "false"
      }
    }
  }
}
```
Antigravity automatically discovers and binds the 5 core tools:
- `search_codebase`: Sub-symbol AST retrieval with 1-hop dependencies.
- `apply_git_patch`: Sandboxed patch application with syntax pre-gate and rollback.
- `run_test_suite`: Sanitized test execution with frame stripping.
- `research_technology`: 5-Phase CRAG LangGraph engine.
- `search_templates`: Living template stockroom with harvested blueprints.

