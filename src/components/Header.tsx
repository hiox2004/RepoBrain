import React from 'react';
import { Cpu, Shield, Terminal, CheckCircle2, Zap, BookOpen, Scale } from 'lucide-react';

interface HeaderProps {
  activeTab: string;
  setActiveTab: (tab: string) => void;
  onRunAllGates: () => void;
  allGatesPassed: boolean;
}

export const Header: React.FC<HeaderProps> = ({
  activeTab,
  setActiveTab,
  onRunAllGates,
  allGatesPassed,
}) => {
  const tabs = [
    { id: 'comparison', label: 'RepoBrain vs Baseline', icon: Scale },
    { id: 'gates', label: '4-Gate Verification', icon: CheckCircle2 },
    { id: 'docs', label: 'Masterguide & Docs', icon: BookOpen },
    { id: 'architecture', label: '3-Layer Architecture', icon: Shield },
    { id: 'ast', label: 'AST Chunker & UTF-8', icon: Cpu },
    { id: 'rrf', label: 'Hybrid RRF (k=60)', icon: Zap },
    { id: 'harness', label: '5-Phase CoT & Sandbox', icon: Terminal },
    { id: 'episodes', label: 'Episodic Memory', icon: Shield },
    { id: 'source', label: 'Prototype Source & SQL', icon: Terminal },
  ];

  return (
    <header className="border-b border-slate-800 bg-slate-950/80 backdrop-blur sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          <div className="flex items-center space-x-3">
            <div className="w-9 h-9 rounded-lg bg-gradient-to-tr from-cyan-500 to-indigo-600 flex items-center justify-center shadow-lg shadow-cyan-500/20">
              <Cpu className="w-5 h-5 text-white" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <span className="font-mono text-base font-bold tracking-tight text-white">RepoBrain</span>
                <span className="px-1.5 py-0.5 text-[10px] font-mono font-semibold uppercase tracking-wider bg-cyan-950 text-cyan-400 border border-cyan-800/80 rounded">
                  FastMCP Core
                </span>
                <span className="px-1.5 py-0.5 text-[10px] font-mono font-semibold uppercase tracking-wider bg-emerald-950 text-emerald-400 border border-emerald-800/80 rounded flex items-center space-x-1">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span>
                  <span>T = 0.0 Deterministic</span>
                </span>
              </div>
              <p className="text-xs text-slate-400 hidden sm:block">
                AST Codebase Memory • Two-Stage RRF Reranking • Bounded 3-Retry Harness • LangGraph CRAG
              </p>
            </div>
          </div>

          <div className="flex items-center space-x-3">
            <button
              onClick={onRunAllGates}
              className={`px-3 py-1.5 rounded-md text-xs font-mono font-medium flex items-center space-x-1.5 transition-all shadow-sm ${
                allGatesPassed
                  ? 'bg-emerald-600 hover:bg-emerald-500 text-white shadow-emerald-500/20'
                  : 'bg-indigo-600 hover:bg-indigo-500 text-white shadow-indigo-500/20'
              }`}
            >
              <Zap className="w-3.5 h-3.5" />
              <span>{allGatesPassed ? 'Re-run 4 Gates' : 'Run 4-Gate Stress Test'}</span>
            </button>
          </div>
        </div>

        {/* Tab Bar */}
        <div className="flex space-x-1 overflow-x-auto pb-2 scrollbar-thin">
          {tabs.map((tab) => {
            const Icon = tab.icon;
            const isActive = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center space-x-1.5 px-3 py-1.5 text-xs font-mono rounded-md whitespace-nowrap transition-colors ${
                  isActive
                    ? 'bg-slate-800 text-cyan-400 border border-slate-700 shadow-inner'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900'
                }`}
              >
                <Icon className={`w-3.5 h-3.5 ${isActive ? 'text-cyan-400' : 'text-slate-400'}`} />
                <span>{tab.label}</span>
              </button>
            );
          })}
        </div>
      </div>
    </header>
  );
};
