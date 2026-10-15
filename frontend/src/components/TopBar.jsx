import React from 'react';
import { 
  Play, 
  Square, 
  ShieldCheck, 
  ShieldAlert, 
  Key, 
  Lock, 
  Compass, 
  Sparkles,
  ExternalLink,
  RotateCcw
} from 'lucide-react';

export default function TopBar({
  targetUrl,
  setTargetUrl,
  isRunning,
  onStart,
  onStop,
  safeMode,
  setSafeMode,
  onOpenAuthModal,
  onOpenKeyModal,
  hasApiKey,
  hasAuthSession,
  wsConnected,
  onReset
}) {
  return (
    <header className="h-16 bg-[#0E1322] border-b border-[#1E293B] px-5 flex items-center justify-between select-none">
      {/* Brand & Tagline */}
      <div className="flex items-center gap-3">
        <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-cyan-500 to-emerald-400 p-[1.5px] shadow-lg shadow-cyan-500/20">
          <div className="w-full h-full bg-[#090D16] rounded-[10px] flex items-center justify-center">
            <Compass className="w-5 h-5 text-cyan-400 animate-spin-slow" />
          </div>
        </div>
        <div>
          <div className="flex items-center gap-2">
            <span className="font-extrabold tracking-wider text-base bg-gradient-to-r from-cyan-400 via-teal-300 to-emerald-400 bg-clip-text text-transparent">
              KARTOS QA
            </span>
            <span className="text-[10px] font-mono uppercase bg-cyan-950/80 text-cyan-400 border border-cyan-800/80 px-1.5 py-0.5 rounded font-semibold tracking-wider">
              Autonomous State-Graph
            </span>
          </div>
          <p className="text-[11px] text-slate-400">
            Set-of-Marks Visual Grounding & Multi-Oracle Telemetry
          </p>
        </div>
      </div>

      {/* Target URL Control */}
      <div className="flex items-center gap-2 flex-1 max-w-xl mx-6">
        <div className="relative w-full">
          <input
            type="text"
            value={targetUrl}
            onChange={(e) => setTargetUrl(e.target.value)}
            placeholder="https://your-app.com or http://localhost:8000/demo"
            disabled={isRunning}
            className="w-full bg-[#090D16] border border-[#1E293B] focus:border-cyan-500 rounded-lg pl-3 pr-24 py-1.5 text-xs font-mono text-slate-200 focus:outline-none transition disabled:opacity-60"
          />
          <button
            onClick={() => setTargetUrl("http://localhost:8000/demo")}
            disabled={isRunning}
            className="absolute right-1.5 top-1.5 text-[10px] font-mono bg-[#1E293B] hover:bg-slate-700 text-cyan-300 px-2 py-0.5 rounded transition flex items-center gap-1"
            title="Load Seeded Buggy Storefront"
          >
            <span>Demo Store</span>
            <ExternalLink className="w-2.5 h-2.5" />
          </button>
        </div>
      </div>

      {/* Actions & Toggles */}
      <div className="flex items-center gap-2.5">
        {/* Gemini API Key Modal Trigger */}
        <button
          onClick={onOpenKeyModal}
          disabled={isRunning}
          className={`px-2.5 py-1.5 rounded-lg text-xs font-mono flex items-center gap-1.5 border transition ${
            hasApiKey
              ? 'bg-emerald-950/40 text-emerald-300 border-emerald-800/60'
              : 'bg-[#090D16] text-slate-400 border-[#1E293B] hover:text-cyan-300'
          }`}
          title="Configure Gemini 2.5 Flash API Key"
        >
          <Sparkles className="w-3.5 h-3.5 text-cyan-400" />
          <span>{hasApiKey ? 'Gemini 2.5' : 'Heuristic Mode'}</span>
        </button>

        {/* Auth / StorageState Modal Trigger */}
        <button
          onClick={onOpenAuthModal}
          disabled={isRunning}
          className={`px-2.5 py-1.5 rounded-lg text-xs font-mono flex items-center gap-1.5 border transition ${
            hasAuthSession
              ? 'bg-cyan-950/40 text-cyan-300 border-cyan-800/60'
              : 'bg-[#090D16] text-slate-400 border-[#1E293B] hover:text-cyan-300'
          }`}
          title="Inject storageState.json / Cookies"
        >
          <Lock className="w-3.5 h-3.5 text-cyan-400" />
          <span>Auth State</span>
        </button>

        {/* Safe Mode Toggle */}
        <button
          onClick={() => setSafeMode(!safeMode)}
          disabled={isRunning}
          className={`px-2.5 py-1.5 rounded-lg text-xs font-mono flex items-center gap-1.5 border transition ${
            safeMode 
              ? 'bg-cyan-950/40 text-cyan-300 border-cyan-800/80 shadow-sm shadow-cyan-950' 
              : 'bg-rose-950/40 text-rose-300 border-rose-800/80'
          }`}
          title="Safe Mode mocks destructive DELETE and checkout requests"
        >
          {safeMode ? (
            <ShieldCheck className="w-3.5 h-3.5 text-cyan-400" />
          ) : (
            <ShieldAlert className="w-3.5 h-3.5 text-rose-400" />
          )}
          <span>{safeMode ? 'Safe Intercept: ON' : 'Safe Intercept: OFF'}</span>
        </button>

        {/* Reset State */}
        <button
          onClick={onReset}
          disabled={isRunning}
          className="p-1.5 rounded-lg bg-[#090D16] border border-[#1E293B] text-slate-400 hover:text-slate-200 transition disabled:opacity-40"
          title="Reset Dashboard and State Graph"
        >
          <RotateCcw className="w-4 h-4" />
        </button>

        {/* WebSocket Pulse Indicator */}
        <div 
          className="flex items-center gap-1 text-[11px] font-mono px-2 py-1 rounded bg-[#090D16] border border-[#1E293B]"
          title={wsConnected ? "WebSocket Connected" : "WebSocket Disconnected"}
        >
          <span className={`w-2 h-2 rounded-full ${wsConnected ? 'bg-emerald-400 animate-pulse' : 'bg-rose-500'}`}></span>
          <span className="text-slate-400 text-[10px]">{wsConnected ? 'LIVE' : 'DISCONNECTED'}</span>
        </div>

        {/* Main Action Button */}
        {isRunning ? (
          <button
            onClick={onStop}
            className="bg-rose-600 hover:bg-rose-500 text-white font-semibold text-xs px-4 py-2 rounded-lg flex items-center gap-1.5 shadow-lg shadow-rose-900/40 transition"
          >
            <Square className="w-3.5 h-3.5 fill-current" />
            <span>Stop Agent</span>
          </button>
        ) : (
          <button
            onClick={onStart}
            className="bg-gradient-to-r from-cyan-500 to-emerald-500 hover:from-cyan-400 hover:to-emerald-400 text-slate-950 font-bold text-xs px-4 py-2 rounded-lg flex items-center gap-1.5 shadow-lg shadow-cyan-500/20 transition transform active:scale-95"
          >
            <Play className="w-3.5 h-3.5 fill-current" />
            <span>Launch Agent</span>
          </button>
        )}
      </div>
    </header>
  );
}
