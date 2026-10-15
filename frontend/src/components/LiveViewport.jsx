import React, { useRef, useEffect } from 'react';
import { Terminal, Eye, Radio, Activity, AlertCircle, CheckCircle2, Cpu } from 'lucide-react';

export default function LiveViewport({
  screenshotB64,
  currentAction,
  logs = [],
  step = 0,
  maxSteps = 10,
  isRunning = false
}) {
  const terminalEndRef = useRef(null);

  useEffect(() => {
    terminalEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [logs]);

  const getTagColor = (tag) => {
    switch (tag) {
      case 'BUG_FOUND':
        return 'bg-rose-950/80 text-rose-400 border-rose-800 animate-pulse';
      case 'PERCEIVE':
        return 'bg-cyan-950/80 text-cyan-400 border-cyan-800';
      case 'GRAPH_HASH':
        return 'bg-purple-950/80 text-purple-400 border-purple-800';
      case 'LLM_DECISION':
      case 'DECISION':
        return 'bg-amber-950/80 text-amber-400 border-amber-800';
      case 'ORACLE_CHECK':
      case 'ORACLE_OK':
        return 'bg-emerald-950/80 text-emerald-400 border-emerald-800';
      case 'SAFE_MODE':
        return 'bg-teal-950/80 text-teal-400 border-teal-800';
      case 'START':
      case 'COMPLETE':
        return 'bg-blue-950/80 text-blue-400 border-blue-800';
      default:
        return 'bg-slate-900 text-slate-400 border-slate-800';
    }
  };

  return (
    <div className="w-[310px] xl:w-[360px] shrink-0 h-full flex flex-col bg-[#090D16] border-r border-[#1E293B]">
      {/* Annotated Viewport Section */}
      <div className="h-[48%] flex flex-col border-b border-[#1E293B]">
        <div className="h-10 px-4 bg-[#0E1322] border-b border-[#1E293B] flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Eye className="w-4 h-4 text-cyan-400" />
            <span className="text-xs font-bold uppercase tracking-wider text-slate-200">
              Live SoM Viewport
            </span>
          </div>
          <div className="flex items-center gap-2 text-[11px] font-mono">
            {isRunning && (
              <span className="flex items-center gap-1 text-cyan-400 bg-cyan-950/60 px-2 py-0.5 rounded border border-cyan-800/60">
                <Radio className="w-3 h-3 animate-ping" />
                Step {step}/{maxSteps}
              </span>
            )}
            <span className="text-slate-400 bg-slate-900 px-2 py-0.5 rounded border border-slate-800">
              1280x800
            </span>
          </div>
        </div>

        {/* Browser Screen Container */}
        <div className="flex-1 bg-[#05070C] relative flex items-center justify-center overflow-hidden p-2 group">
          {screenshotB64 ? (
            <div className="relative w-full h-full flex items-center justify-center">
              <img
                src={`data:image/png;base64,${screenshotB64}`}
                alt="Set-of-Marks Live Frame"
                className="max-h-full max-w-full object-contain rounded border border-slate-800 shadow-2xl"
              />
              {/* Scanline effect while running */}
              {isRunning && (
                <div className="absolute inset-0 pointer-events-none bg-gradient-to-b from-transparent via-cyan-500/10 to-transparent h-16 w-full animate-scanline"></div>
              )}
            </div>
          ) : (
            <div className="text-center p-6 space-y-3">
              <div className="w-12 h-12 mx-auto rounded-full bg-slate-900 border border-slate-800 flex items-center justify-center text-slate-600">
                <Cpu className="w-6 h-6 animate-pulse" />
              </div>
              <p className="text-xs text-slate-400 font-medium">Agent Idle</p>
              <p className="text-[11px] text-slate-600 max-w-xs">
                Launch the agent to stream real-time Set-of-Marks visual bounding boxes and DOM perceptual nodes.
              </p>
            </div>
          )}

          {/* Current Action Banner */}
          {currentAction && (
            <div className="absolute bottom-3 left-3 right-3 bg-[#0E1322]/90 backdrop-blur border border-cyan-800/60 px-3 py-1.5 rounded-lg flex items-center gap-2 shadow-lg">
              <Activity className="w-3.5 h-3.5 text-cyan-400 animate-spin" />
              <span className="text-[11px] font-mono text-cyan-200 truncate">
                {currentAction}
              </span>
            </div>
          )}
        </div>
      </div>

      {/* Real-time Terminal Log Stream */}
      <div className="flex-1 flex flex-col bg-[#070A11] overflow-hidden">
        <div className="h-9 px-4 bg-[#0E1322] border-b border-[#1E293B] flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Terminal className="w-3.5 h-3.5 text-cyan-400" />
            <span className="text-xs font-bold uppercase tracking-wider text-slate-200">
              Agent Perception Log
            </span>
          </div>
          <span className="text-[10px] font-mono text-slate-500">
            {logs.length} events
          </span>
        </div>

        <div className="flex-1 overflow-y-auto p-3 space-y-1.5 font-mono text-xs select-text">
          {logs.length === 0 ? (
            <div className="text-slate-600 text-center py-8 text-[11px]">
              Ready for telemetry stream...
            </div>
          ) : (
            logs.map((log, index) => (
              <div
                key={index}
                className="flex items-start gap-2 py-0.5 hover:bg-slate-900/50 px-1 rounded transition"
              >
                <span
                  className={`text-[9px] font-bold px-1.5 py-0.5 rounded border uppercase shrink-0 ${getTagColor(
                    log.tag
                  )}`}
                >
                  {log.tag}
                </span>
                <span className="text-slate-300 break-words text-[11px] leading-relaxed">
                  {log.message}
                </span>
              </div>
            ))
          )}
          <div ref={terminalEndRef} />
        </div>
      </div>
    </div>
  );
}
