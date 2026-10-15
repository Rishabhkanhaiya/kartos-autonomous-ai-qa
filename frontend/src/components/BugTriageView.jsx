import React, { useState } from 'react';
import { 
  Bug, 
  AlertOctagon, 
  AlertTriangle, 
  Info, 
  Copy, 
  Check, 
  Download, 
  Code2, 
  FileText, 
  Image, 
  ShieldAlert,
  ChevronDown,
  ChevronUp
} from 'lucide-react';

export default function BugTriageView({ bugs = [] }) {
  const [activeTabs, setActiveTabs] = useState({});
  const [copiedId, setCopiedId] = useState(null);
  const [expandedCard, setExpandedCard] = useState(null);

  const getActiveTab = (bugId) => activeTabs[bugId] || 'spec';

  const setTab = (bugId, tab) => {
    setActiveTabs((prev) => ({ ...prev, [bugId]: tab }));
  };

  const copyToClipboard = (text, id) => {
    navigator.clipboard.writeText(text);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  const downloadSpec = (specCode, bugId) => {
    const blob = new Blob([specCode], { type: 'text/typescript' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `reproduce_${bugId.toLowerCase()}.spec.ts`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const getSeverityBadge = (severity) => {
    switch (severity) {
      case 'CRITICAL':
        return 'bg-rose-950/80 text-rose-300 border-rose-800/80';
      case 'HIGH':
        return 'bg-amber-950/80 text-amber-300 border-amber-800/80';
      case 'MEDIUM':
        return 'bg-yellow-950/80 text-yellow-300 border-yellow-800/80';
      default:
        return 'bg-slate-900 text-slate-300 border-slate-800';
    }
  };

  const getOracleBadge = (oracleType) => {
    switch (oracleType) {
      case 'NETWORK_500':
        return 'bg-red-950/60 text-red-400 border-red-800/60';
      case 'CONSOLE_EXCEPTION':
        return 'bg-orange-950/60 text-orange-400 border-orange-800/60';
      case 'SILENT_API_ERROR':
        return 'bg-purple-950/60 text-purple-400 border-purple-800/60';
      case 'VISUAL_ASSET':
        return 'bg-cyan-950/60 text-cyan-400 border-cyan-800/60';
      default:
        return 'bg-slate-900 text-slate-400 border-slate-800';
    }
  };

  const criticalCount = bugs.filter((b) => b.severity === 'CRITICAL').length;
  const highCount = bugs.filter((b) => b.severity === 'HIGH').length;
  const mediumCount = bugs.filter((b) => b.severity === 'MEDIUM').length;

  return (
    <div className="w-[340px] xl:w-[400px] shrink-0 h-full flex flex-col bg-[#090D16] border-l border-[#1E293B]">
      {/* Header */}
      <div className="h-10 px-4 bg-[#0E1322] border-b border-[#1E293B] flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Bug className="w-4 h-4 text-rose-400" />
          <span className="text-xs font-bold uppercase tracking-wider text-slate-200">
            Bug Oracle Triage
          </span>
        </div>
        <div className="flex items-center gap-1.5 text-[10px] font-mono">
          {criticalCount > 0 && (
            <span className="bg-rose-950 text-rose-400 border border-rose-800 px-1.5 py-0.5 rounded font-bold">
              {criticalCount} CRIT
            </span>
          )}
          {highCount > 0 && (
            <span className="bg-amber-950 text-amber-400 border border-amber-800 px-1.5 py-0.5 rounded font-bold">
              {highCount} HIGH
            </span>
          )}
          {mediumCount > 0 && (
            <span className="bg-yellow-950 text-yellow-400 border border-yellow-800 px-1.5 py-0.5 rounded font-bold">
              {mediumCount} MED
            </span>
          )}
          <span className="text-slate-400 bg-slate-900 border border-slate-800 px-1.5 py-0.5 rounded">
            Total: {bugs.length}
          </span>
        </div>
      </div>

      {/* Bug Cards List */}
      <div className="flex-1 overflow-y-auto p-3 space-y-3">
        {bugs.length === 0 ? (
          <div className="h-full flex flex-col items-center justify-center text-center p-6 space-y-3 text-slate-600">
            <div className="w-12 h-12 rounded-full bg-slate-900 border border-slate-800 flex items-center justify-center text-slate-700">
              <ShieldAlert className="w-6 h-6" />
            </div>
            <p className="text-xs font-medium text-slate-500">No Defects Triaged Yet</p>
            <p className="text-[11px] text-slate-600 max-w-xs">
              The multi-oracle engine is listening for HTTP 4xx/5xx crashes, unhandled console exceptions, silent GraphQL errors, and visual asset failures.
            </p>
          </div>
        ) : (
          bugs.map((bug) => {
            const currentTab = getActiveTab(bug.bug_id);
            const isExpanded = expandedCard === bug.bug_id || bugs.length <= 2;

            return (
              <div
                key={bug.bug_id}
                className="bg-[#0E1322] border border-[#1E293B] hover:border-slate-700 rounded-xl overflow-hidden shadow-lg transition"
              >
                {/* Card Title Bar */}
                <div 
                  onClick={() => setExpandedCard(isExpanded && bugs.length > 2 ? null : bug.bug_id)}
                  className="p-3 bg-[#0A0F1D] border-b border-[#1E293B] cursor-pointer flex items-start justify-between gap-2"
                >
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <span className="font-mono text-xs font-extrabold text-cyan-400">
                        {bug.bug_id}
                      </span>
                      <span className={`text-[9px] font-mono font-bold px-1.5 py-0.5 rounded border ${getSeverityBadge(bug.severity)}`}>
                        {bug.severity}
                      </span>
                      <span className={`text-[9px] font-mono px-1.5 py-0.5 rounded border ${getOracleBadge(bug.oracle_type)}`}>
                        {bug.oracle_type}
                      </span>
                    </div>
                    <h4 className="text-xs font-bold text-slate-200 leading-tight">
                      {bug.title}
                    </h4>
                  </div>
                  <button className="text-slate-500 hover:text-slate-300 mt-1">
                    {isExpanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                  </button>
                </div>

                {/* Expanded Details */}
                {isExpanded && (
                  <div>
                    {/* Description */}
                    <div className="p-3 text-[11px] text-slate-400 border-b border-slate-800/80 bg-[#090D16]/50 leading-relaxed font-sans">
                      {bug.description}
                    </div>

                    {/* Tabs navigation */}
                    <div className="flex border-b border-slate-800 bg-[#090D16] text-[10px] font-mono">
                      <button
                        onClick={() => setTab(bug.bug_id, 'spec')}
                        className={`flex-1 py-1.5 px-2 flex items-center justify-center gap-1 border-b-2 transition ${
                          currentTab === 'spec'
                            ? 'border-cyan-400 text-cyan-300 font-bold bg-cyan-950/20'
                            : 'border-transparent text-slate-400 hover:text-slate-200'
                        }`}
                      >
                        <Code2 className="w-3 h-3" />
                        <span>Playwright .spec.ts</span>
                      </button>
                      <button
                        onClick={() => setTab(bug.bug_id, 'har')}
                        className={`flex-1 py-1.5 px-2 flex items-center justify-center gap-1 border-b-2 transition ${
                          currentTab === 'har'
                            ? 'border-cyan-400 text-cyan-300 font-bold bg-cyan-950/20'
                            : 'border-transparent text-slate-400 hover:text-slate-200'
                        }`}
                      >
                        <FileText className="w-3 h-3" />
                        <span>Telemetry</span>
                      </button>
                      <button
                        onClick={() => setTab(bug.bug_id, 'steps')}
                        className={`flex-1 py-1.5 px-2 flex items-center justify-center gap-1 border-b-2 transition ${
                          currentTab === 'steps'
                            ? 'border-cyan-400 text-cyan-300 font-bold bg-cyan-950/20'
                            : 'border-transparent text-slate-400 hover:text-slate-200'
                        }`}
                      >
                        <Info className="w-3 h-3" />
                        <span>Steps ({bug.reproduction_steps?.length || 0})</span>
                      </button>
                      {bug.screenshot_b64 && (
                        <button
                          onClick={() => setTab(bug.bug_id, 'snap')}
                          className={`flex-1 py-1.5 px-2 flex items-center justify-center gap-1 border-b-2 transition ${
                            currentTab === 'snap'
                              ? 'border-cyan-400 text-cyan-300 font-bold bg-cyan-950/20'
                              : 'border-transparent text-slate-400 hover:text-slate-200'
                          }`}
                        >
                          <Image className="w-3 h-3" />
                          <span>Snap</span>
                        </button>
                      )}
                    </div>

                    {/* Tab 1: Playwright Code */}
                    {currentTab === 'spec' && (
                      <div className="relative group">
                        <div className="absolute top-2 right-2 flex items-center gap-1 z-10">
                          <button
                            onClick={() => copyToClipboard(bug.playwright_spec, bug.bug_id)}
                            className="bg-slate-800 hover:bg-slate-700 text-slate-200 p-1.5 rounded text-[10px] font-mono flex items-center gap-1 border border-slate-700 transition"
                            title="Copy code"
                          >
                            {copiedId === bug.bug_id ? (
                              <>
                                <Check className="w-3 h-3 text-emerald-400" />
                                <span className="text-emerald-400">Copied</span>
                              </>
                            ) : (
                              <>
                                <Copy className="w-3 h-3 text-cyan-400" />
                                <span>Copy</span>
                              </>
                            )}
                          </button>
                          <button
                            onClick={() => downloadSpec(bug.playwright_spec, bug.bug_id)}
                            className="bg-slate-800 hover:bg-slate-700 text-slate-200 p-1.5 rounded text-[10px] font-mono flex items-center gap-1 border border-slate-700 transition"
                            title="Download .spec.ts"
                          >
                            <Download className="w-3 h-3 text-cyan-400" />
                          </button>
                        </div>
                        <pre className="p-3 bg-[#05070C] text-[10px] font-mono text-cyan-100 overflow-x-auto max-h-56 leading-relaxed select-text">
                          <code>{bug.playwright_spec}</code>
                        </pre>
                      </div>
                    )}

                    {/* Tab 2: Telemetry / HAR snippet */}
                    {currentTab === 'har' && (
                      <div className="p-3 bg-[#05070C] max-h-56 overflow-y-auto">
                        <pre className="text-[10px] font-mono text-amber-200 leading-relaxed select-text">
                          {JSON.stringify(bug.har_snippet, null, 2)}
                        </pre>
                      </div>
                    )}

                    {/* Tab 3: Reproduction Steps */}
                    {currentTab === 'steps' && (
                      <div className="p-3 bg-[#05070C] max-h-56 overflow-y-auto space-y-1.5">
                        {bug.reproduction_steps?.map((step, idx) => (
                          <div
                            key={idx}
                            className="flex items-start gap-2 text-[11px] font-mono text-slate-300"
                          >
                            <span className="w-4 h-4 rounded-full bg-slate-800 text-cyan-400 text-[9px] flex items-center justify-center shrink-0 font-bold">
                              {idx + 1}
                            </span>
                            <span>{step}</span>
                          </div>
                        ))}
                      </div>
                    )}

                    {/* Tab 4: Screenshot Snapshot */}
                    {currentTab === 'snap' && bug.screenshot_b64 && (
                      <div className="p-2 bg-[#05070C] flex items-center justify-center">
                        <img
                          src={`data:image/png;base64,${bug.screenshot_b64}`}
                          alt="Failure Snapshot"
                          className="max-h-48 rounded border border-slate-800"
                        />
                      </div>
                    )}
                  </div>
                )}
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}
