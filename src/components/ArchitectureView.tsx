import React from 'react';
import { Shield, Layers, Database, Cpu, Terminal, ArrowDown, Lock, CheckCircle2 } from 'lucide-react';
import { GUARDRAILS_SPEC } from '../data/repobrainData';

export const ArchitectureView: React.FC = () => {
  return (
    <div className="space-y-8">
      {/* Hero / Header Card */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 relative overflow-hidden">
        <div className="absolute right-0 top-0 translate-x-12 -translate-y-12 w-96 h-96 bg-cyan-500/10 rounded-full blur-3xl pointer-events-none" />
        <div className="relative z-10 max-w-3xl">
          <div className="inline-flex items-center space-x-2 px-2.5 py-1 rounded-full bg-cyan-950/80 border border-cyan-800 text-cyan-300 text-xs font-mono mb-3">
            <Shield className="w-3.5 h-3.5" />
            <span>REPOBRAIN_MASTER_CONTEXT_SPEC.md Compliant</span>
          </div>
          <h2 className="text-xl sm:text-2xl font-bold text-white tracking-tight">
            End-to-End 3-Layer System Architecture
          </h2>
          <p className="mt-2 text-sm text-slate-300 leading-relaxed">
            RepoBrain connects frontier coding agents (Antigravity IDE, Claude Code, OpenAI Codex, and local open-source models via Ollama/vLLM)
            to local repositories over stdio JSON-RPC without overflowing context windows or permitting unverified, hallucinated code mutations.
          </p>
        </div>
      </div>

      {/* 3-Layer Visual Pipeline */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Layer 1 */}
        <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-5 flex flex-col justify-between hover:border-slate-700 transition">
          <div>
            <div className="flex items-center justify-between mb-3">
              <span className="text-xs font-mono font-semibold uppercase px-2 py-0.5 rounded bg-indigo-950 text-indigo-400 border border-indigo-800/80">
                Layer 1
              </span>
              <Cpu className="w-5 h-5 text-indigo-400" />
            </div>
            <h3 className="text-base font-semibold text-white">Structural Codebase Memory</h3>
            <p className="text-xs text-slate-400 mt-1 mb-4">
              Live AST state indexing Python & TypeScript via concrete syntax trees.
            </p>
            <ul className="space-y-2 text-xs text-slate-300">
              <li className="flex items-start space-x-2">
                <span className="text-cyan-400 font-mono mt-0.5">•</span>
                <span><strong>Parent-Child Split:</strong> Files indexed as <code className="text-cyan-300">ASTParentNode</code>, symbols as <code className="text-cyan-300">ASTChildNode</code>.</span>
              </li>
              <li className="flex items-start space-x-2">
                <span className="text-cyan-400 font-mono mt-0.5">•</span>
                <span><strong>UTF-8 Byte Offset Slicing:</strong> Slices <code className="text-cyan-300">source_bytes[start_byte:end_byte]</code> (Guardrail #1).</span>
              </li>
              <li className="flex items-start space-x-2">
                <span className="text-cyan-400 font-mono mt-0.5">•</span>
                <span><strong>Token Reduction:</strong> Cuts per-symbol token consumption from ~8,000 to 300–600 tokens.</span>
              </li>
              <li className="flex items-start space-x-2">
                <span className="text-cyan-400 font-mono mt-0.5">•</span>
                <span><strong>Live Git SHA Sync:</strong> Transactional PostgreSQL UPSERT with cascading delete (Guardrail #6).</span>
              </li>
            </ul>
          </div>
          <div className="mt-4 pt-3 border-t border-slate-800 text-[11px] font-mono text-indigo-300">
            pgvector HNSW + GIN tsvector
          </div>
        </div>

        {/* Layer 2 */}
        <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-5 flex flex-col justify-between hover:border-slate-700 transition">
          <div>
            <div className="flex items-center justify-between mb-3">
              <span className="text-xs font-mono font-semibold uppercase px-2 py-0.5 rounded bg-amber-950 text-amber-400 border border-amber-800/80">
                Layer 2
              </span>
              <Database className="w-5 h-5 text-amber-400" />
            </div>
            <h3 className="text-base font-semibold text-white">Episodic Diagnostic Memory</h3>
            <p className="text-xs text-slate-400 mt-1 mb-4">
              Self-correcting bug cache distilling fail-to-pass transitions.
            </p>
            <ul className="space-y-2 text-xs text-slate-300">
              <li className="flex items-start space-x-2">
                <span className="text-amber-400 font-mono mt-0.5">•</span>
                <span><strong>Failure-to-Resolution Distillation:</strong> Transitions from exit_code != 0 to exit_code == 0 are distilled into <code className="text-amber-300">project_episodes</code>.</span>
              </li>
              <li className="flex items-start space-x-2">
                <span className="text-amber-400 font-mono mt-0.5">•</span>
                <span><strong>Regression Prevention:</strong> Subsequent searches retrieve matching episodic fixes alongside AST blocks.</span>
              </li>
              <li className="flex items-start space-x-2">
                <span className="text-amber-400 font-mono mt-0.5">•</span>
                <span><strong>Zero Repeats:</strong> Prevents recurring precision scale, async teardown, or serialization bugs.</span>
              </li>
            </ul>
          </div>
          <div className="mt-4 pt-3 border-t border-slate-800 text-[11px] font-mono text-amber-300">
            project_episodes distillation
          </div>
        </div>

        {/* Layer 3 */}
        <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-5 flex flex-col justify-between hover:border-slate-700 transition">
          <div>
            <div className="flex items-center justify-between mb-3">
              <span className="text-xs font-mono font-semibold uppercase px-2 py-0.5 rounded bg-emerald-950 text-emerald-400 border border-emerald-800/80">
                Layer 3 & Sandbox
              </span>
              <Terminal className="w-5 h-5 text-emerald-400" />
            </div>
            <h3 className="text-base font-semibold text-white">Bounded Harness & CRAG</h3>
            <p className="text-xs text-slate-400 mt-1 mb-4">
              Bounded 3-retry execution sandbox with non-destructive surgical rollback.
            </p>
            <ul className="space-y-2 text-xs text-slate-300">
              <li className="flex items-start space-x-2">
                <span className="text-emerald-400 font-mono mt-0.5">•</span>
                <span><strong>Pre-Flight Check:</strong> <code className="text-emerald-300">git apply --check</code> validates diffs without consuming retry budget.</span>
              </li>
              <li className="flex items-start space-x-2">
                <span className="text-emerald-400 font-mono mt-0.5">•</span>
                <span><strong>Hard ≤ 3 Ceiling:</strong> Attempt 3 failure surgically restores exact pre-task bytes (never <code className="text-rose-400">git reset --hard</code>).</span>
              </li>
              <li className="flex items-start space-x-2">
                <span className="text-emerald-400 font-mono mt-0.5">•</span>
                <span><strong>Frame Cleaner:</strong> Strips <code className="text-slate-400">site-packages/</code> and <code className="text-slate-400">node_modules/</code> noise.</span>
              </li>
              <li className="flex items-start space-x-2">
                <span className="text-emerald-400 font-mono mt-0.5">•</span>
                <span><strong>Sanctuary Policy:</strong> Blocks lockfiles, migrations, and policy config from modification.</span>
              </li>
            </ul>
          </div>
          <div className="mt-4 pt-3 border-t border-slate-800 text-[11px] font-mono text-emerald-300">
            Per-File Byte Snapshot & Rollback
          </div>
        </div>
      </div>

      {/* The 8 Non-Negotiable Production Engineering Guardrails */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
        <div className="flex items-center space-x-2 mb-4">
          <Lock className="w-5 h-5 text-cyan-400" />
          <h3 className="text-lg font-bold text-white">The 8 Non-Negotiable Production Engineering Guardrails</h3>
        </div>
        <p className="text-xs text-slate-400 mb-6">
          Discovered during critical systems engineering audits. Every module in RepoBrain strictly complies with these 8 invariants.
        </p>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {GUARDRAILS_SPEC.map((g) => (
            <div key={g.id} className="p-4 rounded-lg bg-slate-950/60 border border-slate-800/80 hover:border-slate-700 transition">
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs font-mono font-bold text-cyan-400">
                  Guardrail #{g.id}
                </span>
                <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700">
                  {g.badge}
                </span>
              </div>
              <h4 className="text-sm font-semibold text-slate-200">{g.title}</h4>
              <p className="text-xs text-slate-400 mt-1 leading-relaxed">{g.desc}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
