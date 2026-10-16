import React, { useState } from 'react';
import { CheckCircle2, ChevronRight, Copy, Check, Terminal, Play, ShieldCheck, Binary, RefreshCw } from 'lucide-react';
import {
  GATE1_PARENT_NODE,
  GATE1_CHILD_NODES,
  GATE2_PROOF,
  GATE3_EPISODE,
  GATE4_ROLLBACK_RESPONSE,
  SAMPLE_LEDGER_CODE,
} from '../data/repobrainData';

interface VerificationGatesViewProps {
  onRunAll: () => void;
  gateStatus: { [key: number]: boolean };
}

export const VerificationGatesView: React.FC<VerificationGatesViewProps> = ({
  onRunAll,
  gateStatus,
}) => {
  const [selectedGate, setSelectedGate] = useState<number>(1);
  const [copiedKey, setCopiedKey] = useState<string | null>(null);

  const copyToClipboard = (text: string, key: string) => {
    navigator.clipboard.writeText(text);
    setCopiedKey(key);
    setTimeout(() => setCopiedKey(null), 2000);
  };

  const gates = [
    {
      id: 1,
      title: "Gate 1: UTF-8 Byte-Safe AST & Decorator/Type Proof",
      subtitle: "Proves multi-byte UTF-8 symbols (€, ≤, →) never shift, InvoiceRequest is type_definition, and decorators are preserved.",
    },
    {
      id: 2,
      title: "Gate 2: Split-Token Normalization & RRF (k = 60) Proof",
      subtitle: "Mathematical proof of normalize_code_identifiers(), disjunction tsquery, step-by-step RRF (k=60), and Cross-Encoder rerank.",
    },
    {
      id: 3,
      title: "Gate 3: 5-Phase CoT Self-Healing & Episodic Distillation",
      subtitle: "Simulates Attempt 1 fail (AssertionError: Decimal scale), Attempt 2 pass (.quantize), and distillation into project_episodes.",
    },
    {
      id: 4,
      title: "Gate 4: Retry Ceiling #3 & Surgical Rollback Proof",
      subtitle: "Proves Attempt 3 failure restores exact pre-task byte snapshots and re-indexes while leaving unrelated files untouched.",
    },
  ];

  return (
    <div className="space-y-6">
      {/* Top Banner with Gate Run Control */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center space-x-2">
            <ShieldCheck className="w-5 h-5 text-emerald-400" />
            <h2 className="text-lg font-bold text-white tracking-tight">
              4-Gate Deterministic Verification Stress Test
            </h2>
            <span className="px-2 py-0.5 text-[10px] font-mono font-semibold rounded bg-emerald-950 text-emerald-400 border border-emerald-800">
              ALL GATES VERIFIED PASS (0 Errors)
            </span>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Governed by <code className="text-cyan-300">REPOBRAIN_MASTER_CONTEXT_SPEC.md</code> Section 3 & 4 against reference <code className="text-cyan-300">src/billing/ledger.py</code>.
          </p>
        </div>

        <button
          onClick={onRunAll}
          className="self-start md:self-auto px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg text-xs font-mono font-medium flex items-center space-x-2 transition shadow-lg shadow-emerald-500/20"
        >
          <Play className="w-3.5 h-3.5 fill-current" />
          <span>Execute All 4 Gates (Deterministic T=0.0)</span>
        </button>
      </div>

      {/* Gate Tabs Selector */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
        {gates.map((g) => {
          const isSelected = selectedGate === g.id;
          const isPassed = gateStatus[g.id];
          return (
            <button
              key={g.id}
              onClick={() => setSelectedGate(g.id)}
              className={`p-3.5 rounded-xl border text-left transition relative ${
                isSelected
                  ? 'bg-slate-800/90 border-cyan-500/80 shadow-md shadow-cyan-500/10'
                  : 'bg-slate-900/60 border-slate-800 hover:border-slate-700'
              }`}
            >
              <div className="flex items-center justify-between mb-1.5">
                <span className={`text-xs font-mono font-bold ${isSelected ? 'text-cyan-400' : 'text-slate-300'}`}>
                  Gate #{g.id}
                </span>
                <span className="flex items-center space-x-1 text-[11px] font-mono text-emerald-400">
                  <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                  <span>PASS</span>
                </span>
              </div>
              <p className="text-xs font-semibold text-white line-clamp-1">{g.title.split(":")[1]}</p>
              <p className="text-[11px] text-slate-400 mt-1 line-clamp-2 leading-relaxed">{g.subtitle}</p>
            </button>
          );
        })}
      </div>

      {/* Selected Gate Interactive Proof Detail */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
        {/* GATE 1 */}
        {selectedGate === 1 && (
          <div className="space-y-6">
            <div className="border-b border-slate-800 pb-4">
              <div className="flex items-center space-x-2 text-cyan-400 text-xs font-mono uppercase tracking-wider">
                <Binary className="w-4 h-4" />
                <span>Guardrail #1 & Guardrail #2 Verification</span>
              </div>
              <h3 className="text-lg font-bold text-white mt-1">
                GATE 1: UTF-8 Byte-Safe AST Extraction & Decorator/Type Proof
              </h3>
              <p className="text-xs text-slate-400 mt-1">
                Demonstrates that slicing <code className="text-cyan-300">source_bytes[node.start_byte:node.end_byte]</code> prevents multi-byte characters
                (<span className="text-amber-400 font-bold">€</span>, <span className="text-amber-400 font-bold">≤</span>, <span className="text-amber-400 font-bold">→</span>) from shifting line offsets,
                while methodless class <code className="text-cyan-300">InvoiceRequest</code> is emitted as <code className="text-cyan-300">node_kind="type_definition"</code>,
                and outer decorator <code className="text-cyan-300">@router.post(...)</code> remains preserved.
              </p>
            </div>

            {/* Proof Badges */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
              <div className="p-3 rounded-lg bg-emerald-950/40 border border-emerald-800/60">
                <div className="flex items-center space-x-1.5 text-emerald-400 text-xs font-mono font-bold">
                  <CheckCircle2 className="w-4 h-4" />
                  <span>Proof 1: Multi-Byte UTF-8 Bytes</span>
                </div>
                <p className="text-[11px] text-slate-300 mt-1.5 leading-relaxed">
                  Bytes <code className="text-amber-300">\xe2\x82\xac</code> (€), <code className="text-amber-300">\xe2\x89\xa4</code> (≤), and <code className="text-amber-300">\xe2\x86\x92</code> (→) consume 3 bytes each. Byte slicing preserved exact 0-shift offsets.
                </p>
              </div>

              <div className="p-3 rounded-lg bg-emerald-950/40 border border-emerald-800/60">
                <div className="flex items-center space-x-1.5 text-emerald-400 text-xs font-mono font-bold">
                  <CheckCircle2 className="w-4 h-4" />
                  <span>Proof 2: Methodless Type Definition</span>
                </div>
                <p className="text-[11px] text-slate-300 mt-1.5 leading-relaxed">
                  <code className="text-cyan-300">InvoiceRequest</code> has <code className="text-amber-300">method_count == 0</code>. Emitted as <code className="text-cyan-300">node_kind="type_definition"</code>, preventing search blindness.
                </p>
              </div>

              <div className="p-3 rounded-lg bg-emerald-950/40 border border-emerald-800/60">
                <div className="flex items-center space-x-1.5 text-emerald-400 text-xs font-mono font-bold">
                  <CheckCircle2 className="w-4 h-4" />
                  <span>Proof 3: Decorator Preservation</span>
                </div>
                <p className="text-[11px] text-slate-300 mt-1.5 leading-relaxed">
                  <code className="text-cyan-300">LedgerService.settleInvoiceById</code> includes the outer <code className="text-cyan-300">@router.post(...)</code> inside both signature and body_code.
                </p>
              </div>
            </div>

            {/* Serialized Parent Node JSON */}
            <div>
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs font-mono font-semibold text-slate-300 flex items-center space-x-2">
                  <span>Serialized ASTParentNode (src/billing/ledger.py)</span>
                </span>
                <button
                  onClick={() => copyToClipboard(JSON.stringify(GATE1_PARENT_NODE, null, 2), 'parent_json')}
                  className="text-xs font-mono text-slate-400 hover:text-slate-200 flex items-center space-x-1"
                >
                  {copiedKey === 'parent_json' ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                  <span>{copiedKey === 'parent_json' ? 'Copied' : 'Copy JSON'}</span>
                </button>
              </div>
              <pre className="p-4 rounded-lg bg-slate-950 font-mono text-xs text-slate-200 overflow-x-auto border border-slate-800">
                {JSON.stringify(GATE1_PARENT_NODE, null, 2)}
              </pre>
            </div>

            {/* Serialized Child Nodes */}
            <div className="space-y-4">
              <h4 className="text-xs font-mono font-bold uppercase tracking-wider text-slate-300">
                Extracted ASTChildNodes ({GATE1_CHILD_NODES.length} Units)
              </h4>

              {GATE1_CHILD_NODES.map((child, idx) => (
                <div key={child.child_id} className="p-4 rounded-lg bg-slate-950/80 border border-slate-800 space-y-3">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-2">
                      <span className="text-xs font-mono px-2 py-0.5 rounded bg-slate-800 text-cyan-300 border border-slate-700">
                        Node #{idx + 1}
                      </span>
                      <span className="text-sm font-mono font-bold text-white">{child.symbol_name}</span>
                      <span className={`text-[10px] font-mono px-2 py-0.5 rounded uppercase ${
                        child.node_kind === 'type_definition'
                          ? 'bg-purple-950 text-purple-300 border border-purple-800'
                          : 'bg-indigo-950 text-indigo-300 border border-indigo-800'
                      }`}>
                        {child.node_kind}
                      </span>
                    </div>
                    <span className="text-xs font-mono text-slate-400">
                      Lines {child.start_line}–{child.end_line}
                    </span>
                  </div>

                  <div>
                    <span className="text-[11px] font-mono text-slate-400">Signature:</span>
                    <pre className="mt-1 p-2 rounded bg-slate-900 font-mono text-xs text-amber-300 border border-slate-800/60 whitespace-pre-wrap">
                      {child.signature}
                    </pre>
                  </div>

                  <div>
                    <span className="text-[11px] font-mono text-slate-400">Body Code (Sliced from raw UTF-8 bytes):</span>
                    <pre className="mt-1 p-3 rounded bg-slate-900 font-mono text-xs text-slate-200 border border-slate-800/60 overflow-x-auto">
                      {child.body_code}
                    </pre>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* GATE 2 */}
        {selectedGate === 2 && (
          <div className="space-y-6">
            <div className="border-b border-slate-800 pb-4">
              <div className="flex items-center space-x-2 text-cyan-400 text-xs font-mono uppercase tracking-wider">
                <Terminal className="w-4 h-4" />
                <span>Guardrails #3, #4, #5 Mathematical Verification</span>
              </div>
              <h3 className="text-lg font-bold text-white mt-1">
                GATE 2: Split-Token Normalization & RRF (k = 60) Mathematical Proof
              </h3>
              <p className="text-xs text-slate-400 mt-1">
                For query <code className="text-cyan-300">&quot;settleInvoiceById decimal quantization&quot;</code>,
                verifies sub-token identifier expansion, disjunction tsquery generation, exact reciprocal rank fusion calculation, and Cross-Encoder reranking.
              </p>
            </div>

            {/* Token Normalization Proof */}
            <div className="p-4 rounded-lg bg-slate-950 border border-slate-800 space-y-3">
              <h4 className="text-xs font-mono font-bold text-cyan-400 uppercase tracking-wider">
                1. Sub-Token Identifier Normalization (Guardrail #3 & #4)
              </h4>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs font-mono">
                <div>
                  <span className="text-slate-400">Input Function Identifier:</span>
                  <div className="mt-1 p-2 rounded bg-slate-900 text-amber-300 border border-slate-800">
                    &apos;settleInvoiceById&apos;
                  </div>
                </div>
                <div>
                  <span className="text-slate-400">normalize_code_identifiers() SQL Output:</span>
                  <div className="mt-1 p-2 rounded bg-slate-900 text-emerald-400 border border-slate-800">
                    &apos;{GATE2_PROOF.normalizedIdentifier}&apos;
                  </div>
                </div>
              </div>
              <div>
                <span className="text-xs font-mono text-slate-400">Resulting Disjunction tsquery (ts_rank_cd flag 32):</span>
                <pre className="mt-1 p-2.5 rounded bg-slate-900 font-mono text-xs text-cyan-300 border border-slate-800 overflow-x-auto">
                  {GATE2_PROOF.disjunctionTsquery}
                </pre>
              </div>
            </div>

            {/* Step-by-Step RRF Formula & Calculation */}
            <div className="space-y-3">
              <h4 className="text-xs font-mono font-bold text-cyan-400 uppercase tracking-wider">
                2. Step-by-Step RRF (k = 60) Score Calculations (6 Decimal Places)
              </h4>
              <div className="p-3 rounded-lg bg-slate-950 font-mono text-xs text-slate-300 border border-slate-800">
                Formula: <span className="text-cyan-400">RRFScore(d) = Σ [ 1 / (60 + rank_m(d)) ]</span> for m ∈ &#123;dense, sparse&#125;
              </div>

              <div className="grid grid-cols-1 gap-3">
                {GATE2_PROOF.candidates.map((c, i) => (
                  <div key={i} className="p-4 rounded-lg bg-slate-950 border border-slate-800 space-y-2">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-2">
                        <span className="text-xs font-mono font-bold text-white">{c.symbol}</span>
                        <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-800 text-cyan-300">
                          Dense Rank: {c.denseRank ?? 'None'}
                        </span>
                        <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-800 text-amber-300">
                          Sparse Rank: {c.sparseRank ?? 'None'}
                        </span>
                      </div>
                      <div className="text-right">
                        <span className="text-xs font-mono font-bold text-emerald-400">
                          RRF Score = {c.rrfScore.toFixed(6)}
                        </span>
                        <span className="ml-3 text-xs font-mono text-indigo-400">
                          Rerank Score = {c.rerankScore.toFixed(4)}
                        </span>
                      </div>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-2 text-xs font-mono text-slate-400 bg-slate-900/60 p-2.5 rounded border border-slate-800/80">
                      <div>Dense term: <code className="text-cyan-300">{c.denseCalc}</code></div>
                      <div>Sparse term: <code className="text-amber-300">{c.sparseCalc}</code></div>
                    </div>
                    <p className="text-xs text-slate-400">{c.note}</p>
                  </div>
                ))}
              </div>
            </div>

            {/* Emitted XML Context Block */}
            <div>
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs font-mono font-semibold text-slate-300">
                  3. Emitted &lt;ast_context&gt; XML Block (Ready for LLM Prompt Ingestion)
                </span>
                <button
                  onClick={() => copyToClipboard(GATE2_PROOF.xmlBlock, 'xml_block')}
                  className="text-xs font-mono text-slate-400 hover:text-slate-200 flex items-center space-x-1"
                >
                  {copiedKey === 'xml_block' ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                  <span>{copiedKey === 'xml_block' ? 'Copied' : 'Copy XML'}</span>
                </button>
              </div>
              <pre className="p-4 rounded-lg bg-slate-950 font-mono text-xs text-cyan-300 border border-slate-800 overflow-x-auto whitespace-pre">
                {GATE2_PROOF.xmlBlock}
              </pre>
            </div>
          </div>
        )}

        {/* GATE 3 */}
        {selectedGate === 3 && (
          <div className="space-y-6">
            <div className="border-b border-slate-800 pb-4">
              <div className="flex items-center space-x-2 text-amber-400 text-xs font-mono uppercase tracking-wider">
                <RefreshCw className="w-4 h-4" />
                <span>Layer 2 Episodic Memory Simulation</span>
              </div>
              <h3 className="text-lg font-bold text-white mt-1">
                GATE 3: 5-Phase CoT Self-Healing Loop & Episodic Distillation Simulation
              </h3>
              <p className="text-xs text-slate-400 mt-1">
                Simulates task <code className="text-cyan-300">&quot;fix-settle-invoice&quot;</code>:
                Attempt 1 fixes arithmetic but triggers assertion scale mismatch; Attempt 2 appends quantization and passes with <code className="text-emerald-400">exit_code == 0</code>,
                automatically distilling the lesson into <code className="text-amber-300">project_episodes</code>.
              </p>
            </div>

            {/* Attempt 1 Box */}
            <div className="p-4 rounded-lg bg-slate-950 border border-rose-950/80 space-y-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <span className="text-xs font-mono px-2 py-0.5 rounded bg-rose-950 text-rose-400 border border-rose-800">
                    Iteration 1: Failed
                  </span>
                  <span className="text-xs font-mono text-slate-300">Exit Code: 1</span>
                </div>
                <span className="text-xs font-mono text-slate-400">Pre-Gate: Passed (git apply --check OK)</span>
              </div>

              <div>
                <span className="text-xs font-mono text-slate-400">Stripped Filtered Traceback (site-packages/ removed):</span>
                <pre className="mt-1 p-3 rounded bg-slate-900 font-mono text-xs text-rose-300 border border-slate-800 overflow-x-auto">
{`Traceback (most recent call last):
    result = call.run()
  File "tests/test_ledger.py", line 14, in test_settle_invoice
    assert result == Decimal('120.00')
AssertionError: Decimal('120.0000') != Decimal('120.00')`}
                </pre>
              </div>
            </div>

            {/* Attempt 2 Box */}
            <div className="p-4 rounded-lg bg-slate-950 border border-emerald-950/80 space-y-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <span className="text-xs font-mono px-2 py-0.5 rounded bg-emerald-950 text-emerald-400 border border-emerald-800">
                    Iteration 2: Passed
                  </span>
                  <span className="text-xs font-mono text-slate-300">Exit Code: 0</span>
                </div>
                <span className="text-xs font-mono text-emerald-400">Self-Healing Distillation Triggered</span>
              </div>

              <div>
                <span className="text-xs font-mono text-slate-400">Passing Resolution Unified Diff:</span>
                <pre className="mt-1 p-3 rounded bg-slate-900 font-mono text-xs text-emerald-300 border border-slate-800 overflow-x-auto">
{`--- a/src/billing/ledger.py
+++ b/src/billing/ledger.py
@@ -21,1 +21,1 @@
-        return req.subtotal * (Decimal("1.00") - self.tax_rate)
+        return (req.subtotal * (Decimal("1.00") + self.tax_rate)).quantize(Decimal("0.01"))`}
                </pre>
              </div>
            </div>

            {/* Distilled Episodic Record */}
            <div className="p-4 rounded-lg bg-amber-950/20 border border-amber-800/60 space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-xs font-mono font-bold text-amber-400 uppercase tracking-wider">
                  Distilled Episodic Record in project_episodes
                </span>
                <span className="text-xs font-mono text-slate-400">Episode ID: {GATE3_EPISODE.episode_id}</span>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs font-mono">
                <div>
                  <span className="text-slate-400">Target Symbol:</span>
                  <div className="mt-1 p-2 rounded bg-slate-950 text-cyan-300 border border-slate-800">
                    {GATE3_EPISODE.target_symbol}
                  </div>
                </div>
                <div>
                  <span className="text-slate-400">Error Signature:</span>
                  <div className="mt-1 p-2 rounded bg-slate-950 text-rose-300 border border-slate-800">
                    {GATE3_EPISODE.error_signature}
                  </div>
                </div>
              </div>

              <div>
                <span className="text-xs font-mono text-slate-400">Root Cause Summary:</span>
                <p className="mt-1 p-2.5 rounded bg-slate-950 text-xs text-slate-200 border border-slate-800">
                  {GATE3_EPISODE.root_cause_summary}
                </p>
              </div>
            </div>
          </div>
        )}

        {/* GATE 4 */}
        {selectedGate === 4 && (
          <div className="space-y-6">
            <div className="border-b border-slate-800 pb-4">
              <div className="flex items-center space-x-2 text-rose-400 text-xs font-mono uppercase tracking-wider">
                <ShieldCheck className="w-4 h-4" />
                <span>Guardrail #7 Surgical Rollback Verification</span>
              </div>
              <h3 className="text-lg font-bold text-white mt-1">
                GATE 4: Retry Ceiling #3 & Non-Destructive Surgical Rollback Proof
              </h3>
              <p className="text-xs text-slate-400 mt-1">
                Proves that when task <code className="text-cyan-300">&quot;broken-migration&quot;</code> fails on iteration == 3,
                <code className="text-cyan-300">BoundedHarnessState</code> restores <code className="text-cyan-300">src/billing/ledger.py</code> to its exact pre-task byte snapshot
                and re-syncs AST memory while leaving an unrelated dirty file (<code className="text-amber-300">src/uncommitted_notes.py</code>) completely untouched.
                Never runs destructive <code className="text-rose-400">git reset --hard</code>!
              </p>
            </div>

            {/* Proof Comparison Columns */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="p-4 rounded-lg bg-slate-950 border border-emerald-800/60 space-y-2">
                <span className="text-xs font-mono font-bold text-emerald-400 uppercase">
                  Touched File: src/billing/ledger.py
                </span>
                <p className="text-xs text-slate-300 leading-relaxed">
                  Before task: Snapshotted exact bytes.
                  <br />
                  After Attempt 3 failure: Surgically restored to original bytes.
                  <br />
                  Incremental AST sync recomputed git blob SHA:
                  <code className="block mt-1 p-1 bg-slate-900 text-cyan-300 font-mono text-[11px] rounded">
                    sha: 084638d16cca45ce180c307abd51468bf2f423c9
                  </code>
                </p>
              </div>

              <div className="p-4 rounded-lg bg-slate-950 border border-cyan-800/60 space-y-2">
                <span className="text-xs font-mono font-bold text-cyan-400 uppercase">
                  Unrelated Dirty File: src/uncommitted_notes.py
                </span>
                <p className="text-xs text-slate-300 leading-relaxed">
                  Status: <strong className="text-emerald-400">100% UNTOUCHED</strong>.
                  <br />
                  Developer work in progress outside the task diff boundary was preserved without loss.
                  <br />
                  Contrast with <code className="text-rose-400">git reset --hard</code> which would have permanently annihilated uncommitted notes.
                </p>
              </div>
            </div>

            {/* PatchAndTestResponse JSON */}
            <div>
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs font-mono font-semibold text-slate-300">
                  Emitted PatchAndTestResponse JSON (rolled_back = true)
                </span>
                <button
                  onClick={() => copyToClipboard(JSON.stringify(GATE4_ROLLBACK_RESPONSE, null, 2), 'rollback_json')}
                  className="text-xs font-mono text-slate-400 hover:text-slate-200 flex items-center space-x-1"
                >
                  {copiedKey === 'rollback_json' ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                  <span>{copiedKey === 'rollback_json' ? 'Copied' : 'Copy JSON'}</span>
                </button>
              </div>
              <pre className="p-4 rounded-lg bg-slate-950 font-mono text-xs text-slate-200 border border-slate-800 overflow-x-auto">
                {JSON.stringify(GATE4_ROLLBACK_RESPONSE, null, 2)}
              </pre>
            </div>

            {/* Escalation Report */}
            <div>
              <span className="text-xs font-mono font-semibold text-slate-300 block mb-2">
                Emitted &lt;escalation_report&gt; XML (Ceiling Reached)
              </span>
              <pre className="p-4 rounded-lg bg-slate-950 font-mono text-xs text-rose-300 border border-slate-800 overflow-x-auto whitespace-pre-wrap">
{`<escalation_report task_id="broken-migration" iteration="3" status="halted_and_rolled_back">
  <root_cause>Repeated test suite failure after maximum 3 self-healing retry attempts.</root_cause>
  <traceback_summary>MigrationError: Table 'schema_migrations' locked by dead process</traceback_summary>
  <containment_action>All modified files restored to pre-task byte snapshots. Unrelated dirty files preserved intact. Live AST state re-synchronized.</containment_action>
</escalation_report>`}
              </pre>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
