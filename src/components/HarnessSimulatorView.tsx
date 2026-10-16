import React, { useState } from 'react';
import { Terminal, Shield, RefreshCw, AlertTriangle, CheckCircle2, RotateCcw } from 'lucide-react';
import { GATE4_ROLLBACK_RESPONSE } from '../data/repobrainData';

export const HarnessSimulatorView: React.FC = () => {
  const [activePhase, setActivePhase] = useState<number>(1);
  const [currentIteration, setCurrentIteration] = useState<number>(1);
  const [testOutcome, setTestOutcome] = useState<'pass' | 'fail'>('fail');
  const [rolledBack, setRolledBack] = useState<boolean>(false);

  const phases = [
    {
      num: 1,
      tag: "<retrieval_formulation>",
      title: "Phase 1: Retrieval Formulation",
      desc: "Decompose user prompt into exact lexical identifiers + semantic domain keywords, query search_codebase(query=..., top_k=5).",
    },
    {
      num: 2,
      tag: "<ast_context_analysis>",
      title: "Phase 2: AST Context Analysis",
      desc: "Inspect <ast_context> blocks, parent imports, enclosing class scopes, type_definitions, and past episodic bug fixes.",
    },
    {
      num: 3,
      tag: "<minimal_patch_synthesis>",
      title: "Phase 3: Minimal Patch Synthesis",
      desc: "Construct minimal unified diff with --- a/ and +++ b/ headers, preserving outer decorators and respecting sanctuary paths.",
    },
    {
      num: 4,
      tag: "<deterministic_verification>",
      title: "Phase 4: Deterministic Verification",
      desc: "Pre-validate diff with git apply --check, take byte snapshot, apply patch, run static pre-gate, execute test runner, evaluate flags.",
    },
    {
      num: 5,
      tag: "<self_healing_diagnostic>",
      title: "Phase 5: Self-Healing Diagnostic",
      desc: "Analyze filtered traceback (stripped of site-packages/), rely on re-indexed AST line numbers, and loop back to Phase 3 (retries 1..3).",
    },
  ];

  const handleSimulateAttempt = (iter: number, outcome: 'pass' | 'fail') => {
    setCurrentIteration(iter);
    setTestOutcome(outcome);
    if (outcome === 'pass') {
      setActivePhase(4);
      setRolledBack(false);
    } else {
      if (iter >= 3) {
        setRolledBack(true);
        setActivePhase(4);
      } else {
        setActivePhase(5);
        setRolledBack(false);
      }
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
        <div className="flex items-center space-x-2 text-emerald-400 text-xs font-mono uppercase tracking-wider">
          <Terminal className="w-4 h-4" />
          <span>Guardrail #7 & #8 Bounded Sandbox</span>
        </div>
        <h3 className="text-lg font-bold text-white mt-1">
          Mandatory 5-Phase CoT State Machine & Bounded 3-Retry Harness
        </h3>
        <p className="text-xs text-slate-400 mt-1">
          RepoBrain protects developer codebases by testing diffs in an isolated sandbox, enforcing a hard ceiling of ≤ 3 iterations,
          and automatically executing non-destructive surgical byte rollback if Attempt 3 fails.
        </p>
      </div>

      {/* 5-Phase Progression Steps */}
      <div className="grid grid-cols-1 md:grid-cols-5 gap-3">
        {phases.map((p) => {
          const isActive = activePhase === p.num;
          return (
            <button
              key={p.num}
              onClick={() => setActivePhase(p.num)}
              className={`p-3.5 rounded-xl border text-left transition ${
                isActive
                  ? 'bg-slate-800 border-cyan-500 shadow-md shadow-cyan-500/10'
                  : 'bg-slate-900 border-slate-800 hover:border-slate-700'
              }`}
            >
              <div className="flex items-center justify-between mb-1">
                <span className={`text-[10px] font-mono font-bold ${isActive ? 'text-cyan-400' : 'text-slate-400'}`}>
                  Step {p.num}
                </span>
                <span className="text-[9px] font-mono px-1 rounded bg-slate-950 text-slate-400">
                  Phase {p.num}
                </span>
              </div>
              <p className="text-xs font-mono font-bold text-white">{p.tag}</p>
              <p className="text-[11px] text-slate-400 mt-1 line-clamp-2">{p.desc}</p>
            </button>
          );
        })}
      </div>

      {/* Interactive Harness Controls */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 space-y-4">
        <div className="flex items-center justify-between">
          <h4 className="text-xs font-mono font-bold uppercase tracking-wider text-slate-300">
            Interactive Test Runner Simulation
          </h4>
          <span className="text-xs font-mono text-slate-400">
            Iteration Budget: <strong className="text-cyan-400">{currentIteration}/3</strong>
          </span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
          <button
            onClick={() => handleSimulateAttempt(1, 'fail')}
            className={`p-3 rounded-lg border text-left transition ${
              currentIteration === 1 && testOutcome === 'fail'
                ? 'bg-rose-950/40 border-rose-600 text-white'
                : 'bg-slate-950 border-slate-800 hover:border-slate-700 text-slate-300'
            }`}
          >
            <div className="flex items-center justify-between">
              <span className="text-xs font-mono font-bold">Attempt #1 (Fail)</span>
              <span className="text-[10px] font-mono text-rose-400">exit 1</span>
            </div>
            <p className="text-[11px] text-slate-400 mt-1">
              Tests fail with Decimal scale mismatch. Triggers self-healing diagnostic.
            </p>
          </button>

          <button
            onClick={() => handleSimulateAttempt(2, 'pass')}
            className={`p-3 rounded-lg border text-left transition ${
              currentIteration === 2 && testOutcome === 'pass'
                ? 'bg-emerald-950/40 border-emerald-600 text-white'
                : 'bg-slate-950 border-slate-800 hover:border-slate-700 text-slate-300'
            }`}
          >
            <div className="flex items-center justify-between">
              <span className="text-xs font-mono font-bold">Attempt #2 (Pass)</span>
              <span className="text-[10px] font-mono text-emerald-400">exit 0</span>
            </div>
            <p className="text-[11px] text-slate-400 mt-1">
              Appends .quantize(Decimal(&quot;0.01&quot;)). Self-healing succeeds & distills episode.
            </p>
          </button>

          <button
            onClick={() => handleSimulateAttempt(3, 'fail')}
            className={`p-3 rounded-lg border text-left transition ${
              currentIteration === 3 && rolledBack
                ? 'bg-amber-950/40 border-amber-600 text-white'
                : 'bg-slate-950 border-slate-800 hover:border-slate-700 text-slate-300'
            }`}
          >
            <div className="flex items-center justify-between">
              <span className="text-xs font-mono font-bold">Attempt #3 (Ceiling & Rollback)</span>
              <span className="text-[10px] font-mono text-amber-400">rolled_back: true</span>
            </div>
            <p className="text-[11px] text-slate-400 mt-1">
              Ceiling reached. Surgically restores pre-task byte snapshots without git reset --hard.
            </p>
          </button>
        </div>
      </div>

      {/* Phase Details & Output Inspector */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 space-y-4">
        <div className="flex items-center justify-between border-b border-slate-800 pb-3">
          <div className="flex items-center space-x-2">
            <span className="text-xs font-mono font-bold text-cyan-400">
              Active Phase: {phases[activePhase - 1].tag}
            </span>
          </div>
          {rolledBack && (
            <span className="px-2 py-0.5 rounded bg-amber-950 text-amber-400 border border-amber-800 text-[10px] font-mono flex items-center space-x-1">
              <RotateCcw className="w-3 h-3" />
              <span>Surgical Rollback Executed</span>
            </span>
          )}
        </div>

        {/* Phase Content Preview */}
        {activePhase === 1 && (
          <div className="space-y-3">
            <span className="text-xs font-mono text-slate-400">XML Reasoning Formulated:</span>
            <pre className="p-4 rounded-lg bg-slate-950 font-mono text-xs text-cyan-300 border border-slate-800 whitespace-pre-wrap">
{`<retrieval_formulation task_id="fix-settle-invoice">
  <target_lexical_tokens>settleInvoiceById, LedgerService, InvoiceRequest</target_lexical_tokens>
  <semantic_domain_keywords>fastapi router post settle invoice decimal calculation</semantic_domain_keywords>
  <action>invoke search_codebase(query="settleInvoiceById decimal quantization", top_k=5)</action>
</retrieval_formulation>`}
            </pre>
          </div>
        )}

        {activePhase === 2 && (
          <div className="space-y-3">
            <span className="text-xs font-mono text-slate-400">AST Context Analysis:</span>
            <pre className="p-4 rounded-lg bg-slate-950 font-mono text-xs text-amber-300 border border-slate-800 whitespace-pre-wrap">
{`<ast_context_analysis>
  <analyzed_symbol file="src/billing/ledger.py" symbol="LedgerService.settleInvoiceById" lines="17-21" />
  <outer_decorator>@router.post("/v1/invoices/settle") preserved</outer_decorator>
  <data_contract>InvoiceRequest (type_definition: BaseModel)</data_contract>
  <hypothesis>The return statement subtracts self.tax_rate instead of adding it, and lacks .quantize(Decimal("0.01")) for currency accuracy.</hypothesis>
</ast_context_analysis>`}
            </pre>
          </div>
        )}

        {activePhase === 3 && (
          <div className="space-y-3">
            <span className="text-xs font-mono text-slate-400">Synthesized Minimal Patch:</span>
            <pre className="p-4 rounded-lg bg-slate-950 font-mono text-xs text-slate-200 border border-slate-800 whitespace-pre-wrap">
{`<minimal_patch_synthesis>
--- a/src/billing/ledger.py
+++ b/src/billing/ledger.py
@@ -21,1 +21,1 @@
-        return req.subtotal * (Decimal("1.00") - self.tax_rate)
+        return (req.subtotal * (Decimal("1.00") + self.tax_rate)).quantize(Decimal("0.01"))
</minimal_patch_synthesis>`}
            </pre>
          </div>
        )}

        {activePhase === 4 && (
          <div className="space-y-3">
            <span className="text-xs font-mono text-slate-400">Deterministic Verification Response:</span>
            <pre className="p-4 rounded-lg bg-slate-950 font-mono text-xs text-emerald-300 border border-slate-800 overflow-x-auto">
              {JSON.stringify(
                testOutcome === 'pass'
                  ? {
                      task_id: "fix-settle-invoice",
                      iteration: currentIteration,
                      patch_applied: true,
                      static_check_passed: true,
                      tests_passed: true,
                      exit_code: 0,
                      rolled_back: false,
                      filtered_traceback: "test_settle_invoice PASSED [100%]",
                      reindexed_files: ["src/billing/ledger.py"],
                      recorded_episode_id: "729371fc-6612-4532-b0e6-50d219258821"
                    }
                  : GATE4_ROLLBACK_RESPONSE,
                null,
                2
              )}
            </pre>
          </div>
        )}

        {activePhase === 5 && (
          <div className="space-y-3">
            <span className="text-xs font-mono text-slate-400">Self-Healing Diagnostic (Traceback Filtered):</span>
            <pre className="p-4 rounded-lg bg-slate-950 font-mono text-xs text-rose-300 border border-slate-800 whitespace-pre-wrap">
{`<self_healing_diagnostic iteration="1" next_iteration="2">
  <root_cause>AssertionError: Decimal('120.0000') != Decimal('120.00')</root_cause>
  <explanation>Fixing tax arithmetic alone produced 4 decimal places of precision. Currency rounding requires explicit .quantize(Decimal("0.01")).</explanation>
  <reindexed_lines file="src/billing/ledger.py" lines="17-21" />
  <action>Transition to Phase 3 with quantized patch.</action>
</self_healing_diagnostic>`}
            </pre>
          </div>
        )}
      </div>
    </div>
  );
};
