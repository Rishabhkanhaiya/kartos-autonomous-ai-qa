import React, { useState, useEffect, useRef } from 'react';
import TopBar from './components/TopBar';
import LiveViewport from './components/LiveViewport';
import StateGraphView from './components/StateGraphView';
import BugTriageView from './components/BugTriageView';
import AuthModal from './components/AuthModal';
import ApiKeyModal from './components/ApiKeyModal';

const API_BASE = "http://localhost:8000";
const WS_URL = "ws://localhost:8000/ws/run";

export default function App() {
  const [targetUrl, setTargetUrl] = useState("http://localhost:8000/demo");
  const [isRunning, setIsRunning] = useState(false);
  const [safeMode, setSafeMode] = useState(true);
  const [apiKey, setApiKey] = useState("");
  const [storageStateJson, setStorageStateJson] = useState(null);

  // Telemetry state
  const [screenshotB64, setScreenshotB64] = useState("");
  const [currentAction, setCurrentAction] = useState("");
  const [logs, setLogs] = useState([]);
  const [step, setStep] = useState(0);
  const [maxSteps, setMaxSteps] = useState(10);
  const [graph, setGraph] = useState({ nodes: [], edges: [], current_node_id: null });
  const [bugs, setBugs] = useState([]);
  const [wsConnected, setWsConnected] = useState(false);

  // Modal states
  const [isAuthModalOpen, setIsAuthModalOpen] = useState(false);
  const [isKeyModalOpen, setIsKeyModalOpen] = useState(false);

  const wsRef = useRef(null);

  // WebSocket Connection Management
  useEffect(() => {
    let ws;
    let reconnectTimer;

    const connectWs = () => {
      try {
        ws = new WebSocket(WS_URL);
        wsRef.current = ws;

        ws.onopen = () => {
          setWsConnected(true);
          console.log("[WS] Connected to telemetry gateway");
        };

        ws.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data);
            if (data.type === "telemetry_frame") {
              if (data.screenshot_b64) setScreenshotB64(data.screenshot_b64);
              if (data.current_action) setCurrentAction(data.current_action);
              if (data.graph) setGraph(data.graph);
              if (data.bugs) setBugs(data.bugs);
              if (data.step !== undefined) setStep(data.step);
              if (data.max_steps !== undefined) setMaxSteps(data.max_steps);
            } else if (data.type === "log") {
              setLogs((prev) => [...prev, data]);
              if (data.tag === "START") setIsRunning(true);
              if (data.tag === "COMPLETE" || data.tag === "STOP") setIsRunning(false);
            }
          } catch (e) {
            console.error("[WS] Error parsing message:", e);
          }
        };

        ws.onclose = () => {
          setWsConnected(false);
          reconnectTimer = setTimeout(connectWs, 2000);
        };

        ws.onerror = () => {
          ws.close();
        };
      } catch (err) {
        reconnectTimer = setTimeout(connectWs, 2000);
      }
    };

    connectWs();

    return () => {
      clearTimeout(reconnectTimer);
      if (ws) ws.close();
    };
  }, []);

  const handleStart = async () => {
    try {
      setIsRunning(true);
      setLogs([]);
      setBugs([]);
      setGraph({ nodes: [], edges: [], current_node_id: null });
      setScreenshotB64("");
      setStep(0);

      const res = await fetch(`${API_BASE}/api/run`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          target_url: targetUrl,
          gemini_api_key: apiKey || null,
          max_steps: maxSteps,
          safe_mode: safeMode,
          storage_state_json: storageStateJson
        })
      });

      if (!res.ok) {
        const err = await res.json();
        alert(`Failed to launch agent: ${err.detail || "Server error"}`);
        setIsRunning(false);
      }
    } catch (e) {
      alert(`Network error connecting to backend API: ${e.message}`);
      setIsRunning(false);
    }
  };

  const handleStop = async () => {
    try {
      if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
        wsRef.current.send(JSON.stringify({ type: "stop" }));
      }
      await fetch(`${API_BASE}/api/stop`, { method: "POST" });
    } catch (e) {
      console.error("Error stopping agent:", e);
    }
  };

  const handleReset = () => {
    setLogs([]);
    setBugs([]);
    setGraph({ nodes: [], edges: [], current_node_id: null });
    setScreenshotB64("");
    setCurrentAction("");
    setStep(0);
    setIsRunning(false);
  };

  return (
    <div className="h-screen w-screen flex flex-col bg-[#090D16] text-slate-100 overflow-hidden font-sans">
      {/* Top Engineering Control Bar */}
      <TopBar
        targetUrl={targetUrl}
        setTargetUrl={setTargetUrl}
        isRunning={isRunning}
        onStart={handleStart}
        onStop={handleStop}
        safeMode={safeMode}
        setSafeMode={setSafeMode}
        onOpenAuthModal={() => setIsAuthModalOpen(true)}
        onOpenKeyModal={() => setIsKeyModalOpen(true)}
        hasApiKey={Boolean(apiKey)}
        hasAuthSession={Boolean(storageStateJson)}
        wsConnected={wsConnected}
        onReset={handleReset}
      />

      {/* Main 3-Column Cockpit Layout */}
      <div className="flex-1 flex overflow-hidden">
        {/* Left Panel: Live Annotated SoM Viewport & Terminal Log */}
        <LiveViewport
          screenshotB64={screenshotB64}
          currentAction={currentAction}
          logs={logs}
          step={step}
          maxSteps={maxSteps}
          isRunning={isRunning}
        />

        {/* Center Panel: Live Interactive Directed State-Machine Graph */}
        <StateGraphView
          graph={graph}
          onSelectNode={(node) => console.log("Selected node:", node)}
        />

        {/* Right Panel: Verified Bug Triage & Auto-Generated Playwright Specs */}
        <BugTriageView bugs={bugs} />
      </div>

      {/* Modals */}
      <AuthModal
        isOpen={isAuthModalOpen}
        onClose={() => setIsAuthModalOpen(false)}
        storageStateJson={storageStateJson}
        onSave={setStorageStateJson}
        defaultUrl={targetUrl}
      />

      <ApiKeyModal
        isOpen={isKeyModalOpen}
        onClose={() => setIsKeyModalOpen(false)}
        apiKey={apiKey}
        onSave={setApiKey}
      />
    </div>
  );
}
