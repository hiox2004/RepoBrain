import React, { useState, useRef } from 'react';
import { BookOpen, ExternalLink, RefreshCw, Compass, Sparkles, CheckCircle2 } from 'lucide-react';

export const StudyGuideView: React.FC = () => {
  const iframeRef = useRef<HTMLIFrameElement>(null);
  const [iframeKey, setIframeKey] = useState<number>(0);

  const handleReload = () => {
    setIframeKey((prev) => prev + 1);
  };

  const handleOpenExternal = () => {
    window.open('/study-guide.html', '_blank');
  };

  const handleJumpToSection = (sectionId: string) => {
    if (iframeRef.current && iframeRef.current.contentWindow) {
      try {
        iframeRef.current.contentWindow.location.hash = sectionId;
      } catch {
        // Fallback: update src with hash
        iframeRef.current.src = `/study-guide.html#${sectionId}`;
      }
    }
  };

  const quickJumps = [
    { id: 'm1', label: '01. Why RepoBrain' },
    { id: 'm2', label: '02. UTF-8 AST Slicing' },
    { id: 'm5', label: '05. Two-Stage RRF' },
    { id: 'm6', label: '06. Episodic Memory' },
    { id: 'm9', label: '09. FastMCP stdio' },
    { id: 'm12', label: '12. LangGraph CRAG' },
    { id: 'm13', label: '13. Self-Learning Loop' },
    { id: 'm14', label: '14. Multi-Stack Matrix' },
    { id: 'm15', label: '15. Dual-Agent Synergy' },
    { id: 'm11', label: '11. CTO Defense Quiz' },
  ];

  return (
    <div className="flex flex-col h-[calc(100vh-8.5rem)] space-y-3 animate-in fade-in duration-300">
      {/* Top Toolbar */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl px-4 py-3 flex flex-wrap items-center justify-between gap-3 shadow-lg shadow-black/20">
        <div className="flex items-center space-x-3">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-tr from-cyan-500 to-indigo-600 flex items-center justify-center text-white shadow-md shadow-cyan-500/20">
            <BookOpen className="w-4 h-4" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <h2 className="text-sm font-bold text-white font-mono">CTO Masterguide & Interactive Academy</h2>
              <span className="px-2 py-0.5 text-[10px] font-mono font-semibold uppercase bg-cyan-950 text-cyan-400 border border-cyan-800/80 rounded">
                15 In-Depth Modules
              </span>
              <span className="px-2 py-0.5 text-[10px] font-mono font-semibold uppercase bg-emerald-950 text-emerald-400 border border-emerald-800/80 rounded hidden sm:inline-flex items-center space-x-1">
                <CheckCircle2 className="w-2.5 h-2.5" />
                <span>Self-Contained</span>
              </span>
            </div>
            <p className="text-xs text-slate-400 hidden sm:block">
              Beginner-to-CTO engineering principles • Live simulators • LangGraph CRAG • Self-learning loops
            </p>
          </div>
        </div>

        <div className="flex items-center space-x-2">
          <button
            onClick={handleReload}
            title="Reload Study Guide"
            className="p-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white transition-colors border border-slate-700 text-xs flex items-center space-x-1.5 font-mono"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            <span className="hidden md:inline">Refresh</span>
          </button>

          <button
            onClick={handleOpenExternal}
            className="px-3 py-1.5 rounded-lg bg-gradient-to-r from-cyan-600 to-indigo-600 hover:from-cyan-500 hover:to-indigo-500 text-white font-mono text-xs font-medium flex items-center space-x-1.5 shadow-md shadow-cyan-500/20 transition-all"
          >
            <ExternalLink className="w-3.5 h-3.5" />
            <span>Open in New Tab</span>
          </button>
        </div>
      </div>

      {/* Quick Jump Ribbon */}
      <div className="flex items-center space-x-1.5 overflow-x-auto pb-1 scrollbar-thin text-xs font-mono">
        <span className="text-slate-400 text-[11px] uppercase tracking-wider flex items-center space-x-1 pr-1 shrink-0">
          <Compass className="w-3 h-3 text-cyan-400" />
          <span>Quick Jump:</span>
        </span>
        {quickJumps.map((q) => (
          <button
            key={q.id}
            onClick={() => handleJumpToSection(q.id)}
            className="px-2.5 py-1 rounded-md bg-slate-900/90 hover:bg-slate-800 text-slate-300 hover:text-cyan-300 border border-slate-800 whitespace-nowrap transition-all text-[11px]"
          >
            {q.label}
          </button>
        ))}
      </div>

      {/* Iframe Viewport */}
      <div className="flex-1 w-full bg-slate-950 border border-slate-800 rounded-xl overflow-hidden shadow-2xl relative">
        <iframe
          key={iframeKey}
          ref={iframeRef}
          src="/study-guide.html"
          title="RepoBrain Interactive Masterguide"
          className="w-full h-full border-0 bg-[#060a12]"
        />
      </div>
    </div>
  );
};

