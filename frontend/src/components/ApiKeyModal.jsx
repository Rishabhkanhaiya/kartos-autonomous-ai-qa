import React, { useState } from 'react';
import { X, Sparkles, Check, Key } from 'lucide-react';

export default function ApiKeyModal({
  isOpen,
  onClose,
  apiKey,
  onSave
}) {
  const [key, setKey] = useState(apiKey || '');

  if (!isOpen) return null;

  const handleSave = () => {
    onSave(key.trim());
    onClose();
  };

  return (
    <div className="fixed inset-0 bg-slate-950/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div className="bg-[#0E1322] border border-[#1E293B] rounded-2xl w-full max-w-md shadow-2xl overflow-hidden">
        <div className="px-5 py-4 border-b border-[#1E293B] flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Sparkles className="w-4 h-4 text-cyan-400" />
            <h3 className="text-sm font-bold text-white">Gemini 2.5 Multimodal Reasoning</h3>
          </div>
          <button onClick={onClose} className="text-slate-400 hover:text-white">
            <X className="w-4 h-4" />
          </button>
        </div>

        <div className="p-5 space-y-3">
          <div className="bg-cyan-950/30 border border-cyan-800/60 rounded-xl p-3 text-xs text-cyan-200 leading-relaxed">
            <span className="font-bold text-cyan-400 block mb-1">Zero-Config Heuristic Fallback Enabled:</span>
            If no API key is provided, the agent runs in <strong>Deterministic State-Graph Explorer Mode</strong>. It explores the UI, handles modals/drawers, and discovers all seeded bugs automatically!
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1.5">
              Google Gemini API Key (Optional)
            </label>
            <div className="relative">
              <Key className="w-4 h-4 text-slate-500 absolute left-3 top-2.5" />
              <input
                type="password"
                value={key}
                onChange={(e) => setKey(e.target.value)}
                placeholder="AIzaSy..."
                className="w-full bg-[#090D16] border border-[#1E293B] focus:border-cyan-500 rounded-xl pl-9 pr-3 py-2 text-xs font-mono text-slate-200 focus:outline-none"
              />
            </div>
            <p className="text-[10px] text-slate-500 mt-1">
              Used for multimodal vision grounding with Set-of-Marks frames.
            </p>
          </div>
        </div>

        <div className="px-5 py-3 border-t border-[#1E293B] bg-[#0A0F1D] flex items-center justify-between">
          <button
            onClick={() => { setKey(''); onSave(''); onClose(); }}
            className="text-xs text-slate-400 hover:text-rose-400 font-mono"
          >
            Use Heuristics Only
          </button>
          <div className="flex items-center gap-2">
            <button
              onClick={onClose}
              className="text-xs px-3 py-1.5 rounded-lg border border-slate-700 text-slate-300 hover:bg-slate-800"
            >
              Cancel
            </button>
            <button
              onClick={handleSave}
              className="text-xs font-semibold px-4 py-1.5 rounded-lg bg-cyan-500 hover:bg-cyan-400 text-slate-950 flex items-center gap-1.5"
            >
              <Check className="w-3.5 h-3.5" />
              Save Key
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
