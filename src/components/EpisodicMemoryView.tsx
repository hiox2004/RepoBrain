import React, { useState } from 'react';
import { Database, Plus, Search, CheckCircle2, ShieldAlert, Sparkles } from 'lucide-react';
import { EpisodicFixRecord } from '../types/repobrain';
import { GATE3_EPISODE } from '../data/repobrainData';

export const EpisodicMemoryView: React.FC = () => {
  const [episodes, setEpisodes] = useState<EpisodicFixRecord[]>([
    GATE3_EPISODE,
    {
      episode_id: "c84180d1-0538-4e92-a162-8bfbce3b0632",
      error_signature: "RuntimeError: Event loop is closed during async client teardown",
      target_symbol: "FastAPIClient.__aexit__",
      file_path: "src/api/client.py",
      root_cause_summary: "Aclosing transport before pending connection pool tasks have yielded causes unhandled CancelledError. Added graceful await client.aclose() with shield.",
      resolution_diff: `--- a/src/api/client.py\n+++ b/src/api/client.py\n@@ -45,1 +45,2 @@\n-        self.transport.close()\n+        if not self.transport.is_closing():\n+            await self.transport.aclose()`,
      created_at: "2026-10-14T18:22:00Z"
    }
  ]);

  const [searchQuery, setSearchQuery] = useState<string>("");
  const [selectedEpisode, setSelectedEpisode] = useState<EpisodicFixRecord>(episodes[0]);

  const filteredEpisodes = episodes.filter((ep) =>
    ep.target_symbol.toLowerCase().includes(searchQuery.toLowerCase()) ||
    ep.error_signature.toLowerCase().includes(searchQuery.toLowerCase()) ||
    ep.file_path.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
        <div className="flex items-center space-x-2 text-amber-400 text-xs font-mono uppercase tracking-wider">
          <Database className="w-4 h-4" />
          <span>Layer 2 Self-Correcting Diagnostic Bug Cache</span>
        </div>
        <h3 className="text-lg font-bold text-white mt-1">
          Episodic Diagnostic Memory (project_episodes)
        </h3>
        <p className="text-xs text-slate-400 mt-1">
          Whenever the self-healing loop transitions from a failing test to a passing test, RepoBrain serializes the error signature,
          target symbol, root cause summary, and passing resolution diff into PostgreSQL. Subsequent searches inject these records directly into the LLM prompt block.
        </p>
      </div>

      {/* Search and Episode List */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Episodes Column */}
        <div className="space-y-3">
          <div className="relative">
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search past episodes..."
              className="w-full px-3 py-2 bg-slate-900 font-mono text-xs text-white rounded-lg border border-slate-800 focus:outline-none focus:border-amber-500 pl-9"
            />
            <Search className="w-4 h-4 text-slate-500 absolute left-3 top-2.5" />
          </div>

          <div className="space-y-2">
            {filteredEpisodes.map((ep) => {
              const isSelected = ep.episode_id === selectedEpisode.episode_id;
              return (
                <button
                  key={ep.episode_id}
                  onClick={() => setSelectedEpisode(ep)}
                  className={`w-full text-left p-3.5 rounded-xl border transition ${
                    isSelected
                      ? 'bg-slate-800 border-amber-500/80 shadow-md shadow-amber-500/10'
                      : 'bg-slate-900 border-slate-800 hover:border-slate-700'
                  }`}
                >
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-xs font-mono font-bold text-white truncate max-w-[180px]">
                      {ep.target_symbol}
                    </span>
                    <span className="text-[10px] font-mono text-amber-400 bg-amber-950/80 px-1.5 py-0.5 rounded border border-amber-800/80">
                      Distilled
                    </span>
                  </div>
                  <p className="text-[11px] font-mono text-rose-300 line-clamp-1">{ep.error_signature}</p>
                  <p className="text-[10px] text-slate-500 font-mono mt-1">{ep.file_path}</p>
                </button>
              );
            })}
          </div>
        </div>

        {/* Selected Episode Detail */}
        <div className="lg:col-span-2 bg-slate-900 border border-slate-800 rounded-xl p-5 space-y-4">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <div>
              <span className="text-xs font-mono text-slate-400">Episode ID:</span>
              <p className="text-xs font-mono text-amber-400 font-bold">{selectedEpisode.episode_id}</p>
            </div>
            <span className="text-[11px] font-mono text-slate-400">
              Target: <code className="text-cyan-300">{selectedEpisode.target_symbol}</code>
            </span>
          </div>

          <div>
            <span className="text-xs font-mono text-slate-400 block mb-1">Error Signature (Indexed via FTS + GIN):</span>
            <div className="p-3 rounded-lg bg-slate-950 font-mono text-xs text-rose-300 border border-slate-800">
              {selectedEpisode.error_signature}
            </div>
          </div>

          <div>
            <span className="text-xs font-mono text-slate-400 block mb-1">Root Cause Summary:</span>
            <div className="p-3.5 rounded-lg bg-slate-950 font-mono text-xs text-slate-200 border border-slate-800 leading-relaxed">
              {selectedEpisode.root_cause_summary}
            </div>
          </div>

          <div>
            <span className="text-xs font-mono text-slate-400 block mb-1">Passing Resolution Diff:</span>
            <pre className="p-4 rounded-lg bg-slate-950 font-mono text-xs text-emerald-300 border border-slate-800 overflow-x-auto">
              {selectedEpisode.resolution_diff}
            </pre>
          </div>
        </div>
      </div>
    </div>
  );
};
