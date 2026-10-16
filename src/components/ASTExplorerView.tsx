import React, { useState } from 'react';
import { Cpu, FileCode, CheckCircle2, AlertCircle, Sparkles } from 'lucide-react';
import { SAMPLE_LEDGER_CODE, GATE1_CHILD_NODES, GATE1_PARENT_NODE } from '../data/repobrainData';

export const ASTExplorerView: React.FC = () => {
  const [code, setCode] = useState<string>(SAMPLE_LEDGER_CODE);
  const [selectedChildId, setSelectedChildId] = useState<string>(GATE1_CHILD_NODES[0].child_id);

  // Character vs Byte count calculation
  const charCount = code.length;
  const byteCount = new TextEncoder().encode(code).length;
  const multiByteDiff = byteCount - charCount;

  const selectedChild = GATE1_CHILD_NODES.find((c) => c.child_id === selectedChildId) || GATE1_CHILD_NODES[0];

  return (
    <div className="space-y-6">
      {/* Header Info */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
        <div className="flex items-center space-x-2 text-cyan-400 text-xs font-mono uppercase tracking-wider">
          <Cpu className="w-4 h-4" />
          <span>Guardrails #1 & #2 Interactive Explorer</span>
        </div>
        <h3 className="text-lg font-bold text-white mt-1">
          UTF-8 Byte Slicing & AST Hierarchical Chunking
        </h3>
        <p className="text-xs text-slate-400 mt-1">
          Inspect how tree-sitter byte offsets prevent character index drift when multi-byte UTF-8 symbols (<span className="text-amber-400">€</span>, <span className="text-amber-400">≤</span>, <span className="text-amber-400">→</span>) are present in docstrings or comments,
          and how outer decorators (<code className="text-cyan-300">@router.post(...)</code>) and methodless classes are cleanly preserved.
        </p>
      </div>

      {/* Metrics Row */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <div className="p-3.5 rounded-xl bg-slate-900 border border-slate-800">
          <span className="text-xs font-mono text-slate-400">UTF-8 Byte Count</span>
          <p className="text-xl font-mono font-bold text-cyan-400 mt-1">{byteCount} bytes</p>
          <span className="text-[10px] text-slate-500 font-mono">Actual file size</span>
        </div>
        <div className="p-3.5 rounded-xl bg-slate-900 border border-slate-800">
          <span className="text-xs font-mono text-slate-400">Character Count</span>
          <p className="text-xl font-mono font-bold text-slate-200 mt-1">{charCount} chars</p>
          <span className="text-[10px] text-slate-500 font-mono">Python len(str)</span>
        </div>
        <div className="p-3.5 rounded-xl bg-slate-900 border border-slate-800">
          <span className="text-xs font-mono text-slate-400">Multi-Byte Delta</span>
          <p className="text-xl font-mono font-bold text-amber-400 mt-1">+{multiByteDiff} bytes</p>
          <span className="text-[10px] text-slate-500 font-mono">3-byte glyphs offset</span>
        </div>
        <div className="p-3.5 rounded-xl bg-slate-900 border border-slate-800">
          <span className="text-xs font-mono text-slate-400">Indexed Children</span>
          <p className="text-xl font-mono font-bold text-emerald-400 mt-1">{GATE1_CHILD_NODES.length} Nodes</p>
          <span className="text-[10px] text-slate-500 font-mono">1 type_def, 2 methods</span>
        </div>
      </div>

      {/* Source Code & Child Node Inspector */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Left Column: Code View */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 flex flex-col">
          <div className="flex items-center justify-between pb-3 border-b border-slate-800 mb-3">
            <div className="flex items-center space-x-2">
              <FileCode className="w-4 h-4 text-cyan-400" />
              <span className="text-xs font-mono font-bold text-slate-200">src/billing/ledger.py</span>
            </div>
            <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-400">
              SHA: {GATE1_PARENT_NODE.git_blob_sha.slice(0, 8)}...
            </span>
          </div>

          <pre className="p-4 rounded-lg bg-slate-950 font-mono text-xs text-slate-300 overflow-x-auto border border-slate-800/80 leading-relaxed flex-1">
            {code.split('\n').map((line, idx) => {
              const lineNo = idx + 1;
              const isHighlighted = lineNo >= selectedChild.start_line && lineNo <= selectedChild.end_line;
              const hasGlyphs = line.includes('€') || line.includes('≤') || line.includes('→');

              return (
                <div
                  key={idx}
                  className={`flex items-start ${
                    isHighlighted ? 'bg-cyan-950/40 -mx-4 px-4 border-l-2 border-cyan-400' : ''
                  }`}
                >
                  <span className="text-slate-600 select-none w-8 text-right pr-3 font-mono text-[11px]">
                    {lineNo}
                  </span>
                  <span className="flex-1 whitespace-pre">
                    {line}
                    {hasGlyphs && (
                      <span className="ml-2 px-1 text-[9px] font-mono bg-amber-950 text-amber-400 rounded border border-amber-800/60 select-none">
                        multi-byte UTF-8
                      </span>
                    )}
                  </span>
                </div>
              );
            })}
          </pre>
        </div>

        {/* Right Column: AST Nodes Inspector */}
        <div className="space-y-4">
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-4">
            <h4 className="text-xs font-mono font-bold uppercase tracking-wider text-slate-400 mb-3">
              AST Parent Context (Imports Header & Scope)
            </h4>
            <div className="p-3 rounded-lg bg-slate-950 border border-slate-800 text-xs font-mono space-y-2">
              <div>
                <span className="text-slate-500">File Path:</span>{' '}
                <span className="text-cyan-300">{GATE1_PARENT_NODE.file_path}</span>
              </div>
              <div>
                <span className="text-slate-500">Git Blob SHA:</span>{' '}
                <span className="text-slate-300">{GATE1_PARENT_NODE.git_blob_sha}</span>
              </div>
              <div>
                <span className="text-slate-500">Imports Header:</span>
                <pre className="mt-1 p-2 rounded bg-slate-900 text-emerald-300 text-[11px]">
                  {GATE1_PARENT_NODE.imports_header}
                </pre>
              </div>
            </div>
          </div>

          <div className="bg-slate-900 border border-slate-800 rounded-xl p-4">
            <h4 className="text-xs font-mono font-bold uppercase tracking-wider text-slate-400 mb-3">
              Select ASTChildNode to Inspect
            </h4>

            <div className="space-y-2">
              {GATE1_CHILD_NODES.map((c) => {
                const isSelected = c.child_id === selectedChildId;
                return (
                  <button
                    key={c.child_id}
                    onClick={() => setSelectedChildId(c.child_id)}
                    className={`w-full text-left p-3 rounded-lg border transition ${
                      isSelected
                        ? 'bg-slate-800/90 border-cyan-500 text-white'
                        : 'bg-slate-950/60 border-slate-800 hover:border-slate-700 text-slate-300'
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-2">
                        <span className="text-xs font-mono font-bold">{c.symbol_name}</span>
                        <span className={`text-[10px] font-mono px-1.5 py-0.2 rounded uppercase ${
                          c.node_kind === 'type_definition'
                            ? 'bg-purple-950 text-purple-300 border border-purple-800'
                            : 'bg-indigo-950 text-indigo-300 border border-indigo-800'
                        }`}>
                          {c.node_kind}
                        </span>
                      </div>
                      <span className="text-[11px] font-mono text-slate-400">
                        Lines {c.start_line}–{c.end_line}
                      </span>
                    </div>
                  </button>
                );
              })}
            </div>

            {/* Selected Node Details */}
            <div className="mt-4 p-3.5 rounded-lg bg-slate-950 border border-slate-800 space-y-2.5">
              <div className="flex items-center justify-between">
                <span className="text-xs font-mono font-bold text-cyan-400">{selectedChild.symbol_name}</span>
                <span className="text-[10px] font-mono text-slate-400">Node ID: {selectedChild.child_id.slice(0, 8)}...</span>
              </div>

              <div>
                <span className="text-[11px] font-mono text-slate-400">Signature:</span>
                <pre className="mt-1 p-2 rounded bg-slate-900 font-mono text-xs text-amber-300 border border-slate-800/60 whitespace-pre-wrap">
                  {selectedChild.signature}
                </pre>
              </div>

              <div>
                <span className="text-[11px] font-mono text-slate-400">Docstring (UTF-8 Verified):</span>
                <p className="mt-1 p-2 rounded bg-slate-900 font-mono text-xs text-slate-300 border border-slate-800/60">
                  {selectedChild.docstring || '(None)'}
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
