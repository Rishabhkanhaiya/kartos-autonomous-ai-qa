import React, { useState, useEffect } from 'react';
import { X, Lock, Check, Sparkles, ExternalLink, RefreshCw, AlertCircle, CheckCircle2 } from 'lucide-react';

export default function AuthModal({
  isOpen,
  onClose,
  storageStateJson,
  onSave,
  defaultUrl = "https://www.flipkart.com/account/login"
}) {
  const [content, setContent] = useState(storageStateJson || '');
  const [recordUrl, setRecordUrl] = useState(defaultUrl);
  const [isRecording, setIsRecording] = useState(false);
  const [recorderStatus, setRecorderStatus] = useState(null); // 'recording', 'success', 'error'
  const [statusMessage, setStatusMessage] = useState('');
  const [error, setError] = useState(null);

  useEffect(() => {
    if (storageStateJson) {
      setContent(storageStateJson);
    }
  }, [storageStateJson]);

  // Polling for recorder status while active
  useEffect(() => {
    let interval;
    if (isRecording) {
      interval = setInterval(async () => {
        try {
          const res = await fetch("http://localhost:8000/api/auth/record-status");
          if (res.ok) {
            const data = await res.json();
            if (data.has_captured && data.storage_state) {
              const jsonStr = JSON.stringify(data.storage_state, null, 2);
              setContent(jsonStr);
              setIsRecording(false);
              setRecorderStatus('success');
              const cookiesCount = data.storage_state.cookies?.length || 0;
              const originsCount = data.storage_state.origins?.length || 0;
              setStatusMessage(`Captured ${cookiesCount} cookies & ${originsCount} local storage keys!`);
              onSave(jsonStr);
            } else if (!data.is_recording && isRecording) {
              setIsRecording(false);
            }
          }
        } catch (e) {
          console.error("Error polling recorder status:", e);
        }
      }, 1500);
    }
    return () => clearInterval(interval);
  }, [isRecording, onSave]);

  if (!isOpen) return null;

  const handleStartRecording = async () => {
    try {
      setIsRecording(true);
      setRecorderStatus('recording');
      setStatusMessage('Opening visible Chromium browser... Log in and solve any OTP/CAPTCHA, then click "Capture & Save Session" in the top banner.');

      const res = await fetch("http://localhost:8000/api/auth/record-start", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url: recordUrl || "https://www.flipkart.com" })
      });

      if (!res.ok) {
        setIsRecording(false);
        setRecorderStatus('error');
        setStatusMessage('Failed to launch recorder browser.');
      }
    } catch (e) {
      setIsRecording(false);
      setRecorderStatus('error');
      setStatusMessage(`Error: ${e.message}`);
    }
  };

  const handleManualCapture = async () => {
    try {
      setStatusMessage('Capturing current session from browser...');
      const res = await fetch("http://localhost:8000/api/auth/record-finish", { method: "POST" });
      if (res.ok) {
        const data = await res.json();
        if (data.storage_state) {
          const jsonStr = JSON.stringify(data.storage_state, null, 2);
          setContent(jsonStr);
          setIsRecording(false);
          setRecorderStatus('success');
          const cookiesCount = data.storage_state.cookies?.length || 0;
          const originsCount = data.storage_state.origins?.length || 0;
          setStatusMessage(`Successfully captured ${cookiesCount} cookies & ${originsCount} origins!`);
          onSave(jsonStr);
        }
      }
    } catch (e) {
      setStatusMessage(`Error capturing session: ${e.message}`);
    }
  };

  const handleCancelRecording = async () => {
    try {
      await fetch("http://localhost:8000/api/auth/record-cancel", { method: "POST" });
    } catch (e) {}
    setIsRecording(false);
    setRecorderStatus(null);
    setStatusMessage('');
  };

  const handleSave = () => {
    if (!content.trim()) {
      onSave(null);
      onClose();
      return;
    }
    try {
      JSON.parse(content);
      setError(null);
      onSave(content);
      onClose();
    } catch (e) {
      setError('Invalid JSON syntax. Please paste a valid Playwright storageState JSON object.');
    }
  };

  const loadSample = () => {
    const sample = {
      cookies: [
        {
          name: "auth_token",
          value: "jwt_ey8912389127391.dummy.token",
          domain: "localhost",
          path: "/",
          expires: -1,
          httpOnly: true,
          secure: false,
          sameSite: "Lax"
        }
      ],
      origins: [
        {
          origin: "http://localhost:8000",
          localStorage: [
            {
              name: "user_session",
              value: JSON.stringify({ userId: "usr_4921", role: "qa_tester", plan: "enterprise" })
            }
          ]
        }
      ]
    };
    setContent(JSON.stringify(sample, null, 2));
    setError(null);
  };

  return (
    <div className="fixed inset-0 bg-slate-950/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div className="bg-[#0E1322] border border-[#1E293B] rounded-2xl w-full max-w-xl shadow-2xl overflow-hidden max-h-[90vh] flex flex-col">
        {/* Header */}
        <div className="px-5 py-4 border-b border-[#1E293B] flex items-center justify-between shrink-0">
          <div className="flex items-center gap-2">
            <Lock className="w-4 h-4 text-cyan-400" />
            <h3 className="text-sm font-bold text-white">Auth Session State (storageState.json)</h3>
          </div>
          <button onClick={onClose} className="text-slate-400 hover:text-white">
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Scrollable Body */}
        <div className="p-5 space-y-4 overflow-y-auto flex-1">
          {/* Section 1: Interactive One-Click Session Recorder */}
          <div className="bg-gradient-to-br from-cyan-950/40 via-[#0B132B]/60 to-emerald-950/30 border border-cyan-800/60 rounded-xl p-4 space-y-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Sparkles className="w-4 h-4 text-cyan-400" />
                <span className="text-xs font-bold text-cyan-200">
                  Interactive One-Click Session Recorder
                </span>
              </div>
              <span className="text-[10px] font-mono uppercase bg-emerald-950 text-emerald-400 border border-emerald-800/80 px-2 py-0.5 rounded font-bold">
                Automated 2FA / OTP Bypass
              </span>
            </div>

            <p className="text-[11px] text-slate-300 leading-relaxed">
              Launches a real visible browser window. Log in manually (solve 2FA, OTP, or Google SSO), and Kartos automatically captures and injects your cookies into the autonomous agent!
            </p>

            <div className="flex gap-2">
              <input
                type="text"
                value={recordUrl}
                onChange={(e) => setRecordUrl(e.target.value)}
                placeholder="https://www.flipkart.com/account/login"
                disabled={isRecording}
                className="flex-1 bg-[#090D16] border border-cyan-900/80 rounded-lg px-3 py-1.5 text-xs font-mono text-slate-200 focus:outline-none focus:border-cyan-500"
              />
              {isRecording ? (
                <div className="flex gap-1.5">
                  <button
                    onClick={handleManualCapture}
                    className="bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-bold px-3 py-1.5 rounded-lg text-xs flex items-center gap-1 transition shadow-lg shadow-emerald-950"
                  >
                    <Check className="w-3.5 h-3.5" />
                    <span>Capture Now</span>
                  </button>
                  <button
                    onClick={handleCancelRecording}
                    className="bg-rose-950 border border-rose-800 text-rose-300 px-2.5 py-1.5 rounded-lg text-xs transition"
                  >
                    Cancel
                  </button>
                </div>
              ) : (
                <button
                  onClick={handleStartRecording}
                  className="bg-gradient-to-r from-cyan-500 to-emerald-400 hover:from-cyan-400 hover:to-emerald-300 text-slate-950 font-bold px-3.5 py-1.5 rounded-lg text-xs flex items-center gap-1.5 transition shadow-lg shadow-cyan-950 shrink-0"
                >
                  <ExternalLink className="w-3.5 h-3.5" />
                  <span>Launch Login Window</span>
                </button>
              )}
            </div>

            {/* Recorder Status Banner */}
            {recorderStatus && (
              <div
                className={`p-2.5 rounded-lg text-xs font-mono flex items-start gap-2 border ${
                  recorderStatus === 'recording'
                    ? 'bg-cyan-950/60 text-cyan-200 border-cyan-800 animate-pulse'
                    : recorderStatus === 'success'
                    ? 'bg-emerald-950/70 text-emerald-200 border-emerald-800'
                    : 'bg-rose-950/70 text-rose-200 border-rose-800'
                }`}
              >
                {recorderStatus === 'recording' ? (
                  <RefreshCw className="w-4 h-4 animate-spin text-cyan-400 shrink-0 mt-0.5" />
                ) : recorderStatus === 'success' ? (
                  <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
                ) : (
                  <AlertCircle className="w-4 h-4 text-rose-400 shrink-0 mt-0.5" />
                )}
                <span className="leading-relaxed">{statusMessage}</span>
              </div>
            )}
          </div>

          {/* Section 2: JSON Payload Inspection */}
          <div>
            <div className="flex items-center justify-between mb-1.5">
              <label className="text-xs font-semibold text-slate-300">
                Active Session State JSON
              </label>
              <button
                onClick={loadSample}
                className="text-[10px] font-mono text-cyan-400 hover:underline"
              >
                + Load Mock Dummy Session
              </button>
            </div>

            <textarea
              value={content}
              onChange={(e) => setContent(e.target.value)}
              placeholder='{"cookies": [...], "origins": [...]}'
              rows={7}
              className="w-full bg-[#090D16] border border-[#1E293B] focus:border-cyan-500 rounded-xl p-3 text-xs font-mono text-slate-200 focus:outline-none leading-relaxed"
            />

            {error && (
              <p className="text-xs text-rose-400 font-mono bg-rose-950/40 p-2 rounded border border-rose-900/60 mt-2">
                {error}
              </p>
            )}
          </div>
        </div>

        {/* Footer */}
        <div className="px-5 py-3 border-t border-[#1E293B] bg-[#0A0F1D] flex items-center justify-between shrink-0">
          <button
            onClick={() => { setContent(''); onSave(null); onClose(); }}
            className="text-xs text-slate-400 hover:text-rose-400 font-mono"
          >
            Clear Session
          </button>
          <div className="flex items-center gap-2">
            <button
              onClick={onClose}
              className="text-xs px-3 py-1.5 rounded-lg border border-slate-700 text-slate-300 hover:bg-slate-800"
            >
              Close
            </button>
            <button
              onClick={handleSave}
              className="text-xs font-semibold px-4 py-1.5 rounded-lg bg-cyan-500 hover:bg-cyan-400 text-slate-950 flex items-center gap-1.5"
            >
              <Check className="w-3.5 h-3.5" />
              Save & Apply
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
