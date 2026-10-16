/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import React, { useState } from 'react';
import { Header } from './components/Header';
import { ArchitectureView } from './components/ArchitectureView';
import { VerificationGatesView } from './components/VerificationGatesView';
import { ASTExplorerView } from './components/ASTExplorerView';
import { RRFCalculatorView } from './components/RRFCalculatorView';
import { HarnessSimulatorView } from './components/HarnessSimulatorView';
import { EpisodicMemoryView } from './components/EpisodicMemoryView';
import { SourceCodeView } from './components/SourceCodeView';
import { Shield, CheckCircle2, Terminal, Cpu, Database } from 'lucide-react';

export default function App() {
  const [activeTab, setActiveTab] = useState<string>('gates');
  const [isRunningGates, setIsRunningGates] = useState<boolean>(false);
  const [gateStatus, setGateStatus] = useState<{ [key: number]: boolean }>({
    1: true,
    2: true,
    3: true,
    4: true,
  });
  const [toastMessage, setToastMessage] = useState<string | null>(null);

  const showToast = (msg: string) => {
    setToastMessage(msg);
    setTimeout(() => setToastMessage(null), 3000);
  };

  const handleRunAllGates = () => {
    setIsRunningGates(true);
    showToast("Executing 4-Gate Deterministic Stress Test (T=0.0)...");
    setTimeout(() => {
      setGateStatus({ 1: true, 2: true, 3: true, 4: true });
      setIsRunningGates(false);
      showToast("All 4 Gates verified successfully: 0 errors, 100% compliant.");
    }, 600);
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans selection:bg-cyan-500/30 selection:text-cyan-200">
      {/* Toast Notification */}
      {toastMessage && (
        <div className="fixed bottom-6 right-6 z-50 bg-slate-900 border border-cyan-500/80 text-white px-4 py-2.5 rounded-lg shadow-2xl flex items-center space-x-2 font-mono text-xs animate-in fade-in slide-in-from-bottom-2">
          <CheckCircle2 className="w-4 h-4 text-emerald-400" />
          <span>{toastMessage}</span>
        </div>
      )}

      {/* Main Top Header */}
      <Header
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        onRunAllGates={handleRunAllGates}
        allGatesPassed={Object.values(gateStatus).every(Boolean)}
      />

      {/* Content Container */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {activeTab === 'gates' && (
          <VerificationGatesView
            onRunAll={handleRunAllGates}
            gateStatus={gateStatus}
          />
        )}

        {activeTab === 'architecture' && <ArchitectureView />}

        {activeTab === 'ast' && <ASTExplorerView />}

        {activeTab === 'rrf' && <RRFCalculatorView />}

        {activeTab === 'harness' && <HarnessSimulatorView />}

        {activeTab === 'episodes' && <EpisodicMemoryView />}

        {activeTab === 'source' && <SourceCodeView />}
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-900 bg-slate-950 py-4 px-6 text-xs text-slate-500 font-mono flex flex-col sm:flex-row items-center justify-between gap-2 max-w-7xl mx-auto w-full">
        <div className="flex items-center space-x-2">
          <span className="w-2 h-2 rounded-full bg-emerald-400"></span>
          <span className="text-slate-400">RepoBrain FastMCP Engine</span>
          <span>•</span>
          <span>8 Guardrails Active</span>
          <span>•</span>
          <span>T=0.0 Deterministic</span>
        </div>

        <div className="flex items-center space-x-4">
          <span className="text-slate-400">Target: <code className="text-cyan-400">src/billing/ledger.py</code></span>
          <span>•</span>
          <span className="text-slate-400">RRF: <code className="text-amber-400">k=60</code></span>
          <span>•</span>
          <span className="text-slate-400">Max Retries: <code className="text-emerald-400">≤ 3</code></span>
        </div>
      </footer>
    </div>
  );
}
