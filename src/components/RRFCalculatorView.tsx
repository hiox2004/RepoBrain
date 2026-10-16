import React, { useState } from 'react';
import { Zap, Search, Sliders, ArrowRight, CheckCircle2 } from 'lucide-react';
import { GATE2_PROOF } from '../data/repobrainData';

export const RRFCalculatorView: React.FC = () => {
  const [queryInput, setQueryInput] = useState<string>("settleInvoiceById decimal quantization");
  const [customDenseRank, setCustomDenseRank] = useState<number>(3);
  const [customSparseRank, setCustomSparseRank] = useState<number>(1);
  const [kConstant, setKConstant] = useState<number>(60);

  // Sub-token identifier split calculation simulation
  const normalizeIdentifier = (input: string) => {
    const step1 = input.replace(/([A-Z]+)([A-Z][a-z])/g, '$1 $2');
    const step2 = step1.replace(/([a-z0-9])([A-Z])/g, '$1 $2');
    const step3 = step2.replace(/[_./:-]+/g, ' ');
    const lower = step3.toLowerCase();
    return `${input} ${lower}`.trim();
  };

  const normalized = normalizeIdentifier(queryInput);
  const tokens = Array.from(new Set(normalized.replace(/[^a-zA-Z0-9_]+/g, ' ').split(/\s+/).filter(t => t.length > 1)));
  const tsquery = tokens.map(t => `'${t}'`).join(' | ');

  // Dynamic RRF Calculation
  const denseTerm = 1.0 / (kConstant + customDenseRank);
  const sparseTerm = customSparseRank > 0 ? 1.0 / (kConstant + customSparseRank) : 0.0;
  const totalRRF = denseTerm + sparseTerm;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
        <div className="flex items-center space-x-2 text-cyan-400 text-xs font-mono uppercase tracking-wider">
          <Zap className="w-4 h-4" />
          <span>Guardrails #3, #4, #5 Interactive Engine</span>
        </div>
        <h3 className="text-lg font-bold text-white mt-1">
          Two-Stage Hybrid RRF (k = 60) & Sub-Token Identifier Normalizer
        </h3>
        <p className="text-xs text-slate-400 mt-1">
          Pairing <code className="text-cyan-300">pgvector HNSW cosine distance (&lt;=&gt;)</code> with <code className="text-cyan-300">PostgreSQL tsvector BM25 / GIN</code> index,
          fusing rankings via Reciprocal Rank Fusion, and reranking top 25 candidates with Cross-Encoder.
        </p>
      </div>

      {/* Interactive Query & Normalizer Box */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 space-y-4">
        <h4 className="text-xs font-mono font-bold uppercase tracking-wider text-slate-300">
          1. Sub-Token Identifier Normalizer & Disjunction tsquery Generator
        </h4>

        <div>
          <label className="block text-xs font-mono text-slate-400 mb-1">Interactive Code Query:</label>
          <div className="relative">
            <input
              type="text"
              value={queryInput}
              onChange={(e) => setQueryInput(e.target.value)}
              className="w-full px-3 py-2 bg-slate-950 font-mono text-xs text-white rounded-lg border border-slate-800 focus:outline-none focus:border-cyan-500 pl-9"
              placeholder="Enter search query..."
            />
            <Search className="w-4 h-4 text-slate-500 absolute left-3 top-2.5" />
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="p-3 rounded-lg bg-slate-950 border border-slate-800">
            <span className="text-[11px] font-mono text-slate-400 block mb-1">
              normalize_code_identifiers() Output (Exact Token + Sub-Tokens):
            </span>
            <code className="text-xs font-mono text-emerald-400 break-words">
              {normalized}
            </code>
          </div>

          <div className="p-3 rounded-lg bg-slate-950 border border-slate-800">
            <span className="text-[11px] font-mono text-slate-400 block mb-1">
              Disjunction tsquery (with ts_rank_cd flag 32):
            </span>
            <code className="text-xs font-mono text-cyan-300 break-words">
              {tsquery}
            </code>
          </div>
        </div>
      </div>

      {/* Interactive RRF Math Sandbox */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 space-y-4">
        <div className="flex items-center justify-between">
          <h4 className="text-xs font-mono font-bold uppercase tracking-wider text-slate-300">
            2. Real-Time RRF (k = 60) Score Simulator
          </h4>
          <span className="text-xs font-mono text-cyan-400">
            Score = {totalRRF.toFixed(6)}
          </span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          {/* Dense Rank Slider */}
          <div className="p-4 rounded-lg bg-slate-950 border border-slate-800 space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-xs font-mono text-slate-400">Dense Rank (pgvector)</span>
              <span className="text-xs font-mono font-bold text-cyan-400">#{customDenseRank}</span>
            </div>
            <input
              type="range"
              min="1"
              max="40"
              value={customDenseRank}
              onChange={(e) => setCustomDenseRank(Number(e.target.value))}
              className="w-full accent-cyan-500"
            />
            <span className="text-[11px] font-mono text-slate-500 block">
              Term: 1 / (60 + {customDenseRank}) = {denseTerm.toFixed(8)}
            </span>
          </div>

          {/* Sparse Rank Slider */}
          <div className="p-4 rounded-lg bg-slate-950 border border-slate-800 space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-xs font-mono text-slate-400">Sparse Rank (tsvector)</span>
              <span className="text-xs font-mono font-bold text-amber-400">#{customSparseRank}</span>
            </div>
            <input
              type="range"
              min="1"
              max="40"
              value={customSparseRank}
              onChange={(e) => setCustomSparseRank(Number(e.target.value))}
              className="w-full accent-amber-500"
            />
            <span className="text-[11px] font-mono text-slate-500 block">
              Term: 1 / (60 + {customSparseRank}) = {sparseTerm.toFixed(8)}
            </span>
          </div>

          {/* Fusion Result */}
          <div className="p-4 rounded-lg bg-slate-950 border border-emerald-950/80 flex flex-col justify-between">
            <span className="text-xs font-mono text-slate-400">Fused RRF Score (k=60)</span>
            <div className="text-2xl font-mono font-bold text-emerald-400">
              {totalRRF.toFixed(6)}
            </div>
            <span className="text-[10px] font-mono text-slate-500">
              RRFScore(d) = {denseTerm.toFixed(6)} + {sparseTerm.toFixed(6)}
            </span>
          </div>
        </div>
      </div>

      {/* Verified Benchmark Candidates Comparison */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 space-y-3">
        <h4 className="text-xs font-mono font-bold uppercase tracking-wider text-slate-300">
          3. Verified Benchmark Candidates from Gate 2 Stress Test
        </h4>

        <div className="overflow-x-auto">
          <table className="w-full text-left font-mono text-xs">
            <thead>
              <tr className="border-b border-slate-800 text-slate-400">
                <th className="pb-2">Candidate Symbol</th>
                <th className="pb-2">Dense Rank</th>
                <th className="pb-2">Sparse Rank</th>
                <th className="pb-2">RRF Score (k=60)</th>
                <th className="pb-2">Cross-Encoder</th>
                <th className="pb-2">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {GATE2_PROOF.candidates.map((c, idx) => (
                <tr key={idx} className="hover:bg-slate-950/50">
                  <td className="py-2.5 font-bold text-white">{c.symbol}</td>
                  <td className="py-2.5 text-cyan-300">{c.denseRank}</td>
                  <td className="py-2.5 text-amber-300">{c.sparseRank ?? 'NULL (Unmatched)'}</td>
                  <td className="py-2.5 font-bold text-emerald-400">{c.rrfScore.toFixed(6)}</td>
                  <td className="py-2.5 text-indigo-400">{c.rerankScore.toFixed(4)}</td>
                  <td className="py-2.5">
                    {idx === 0 ? (
                      <span className="px-2 py-0.5 rounded bg-emerald-950 text-emerald-400 border border-emerald-800 text-[10px]">
                        Top Hit (Rank #1)
                      </span>
                    ) : (
                      <span className="text-slate-500 text-[10px]">Pool Candidate</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
