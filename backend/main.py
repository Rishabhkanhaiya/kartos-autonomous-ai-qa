"""
FastAPI Server & WebSocket Telemetry Gateway
Provides REST endpoints and real-time WebSocket streaming for the Autonomous QA & State-Graph Explorer.
"""

import asyncio
import json
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from demo_app import demo_router
from agent_runner import AutonomousAgentRunner
from session_recorder import session_recorder

app = FastAPI(
    title="Autonomous AI QA & State-Graph Explorer API",
    description="Dual-modality Set-of-Marks and State-Graph explorer with multi-oracle CDP telemetry",
    version="1.0.0"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount seeded demo buggy app
app.include_router(demo_router)

# Global execution state
active_runner: Optional[AutonomousAgentRunner] = None
connected_websockets: List[WebSocket] = []

class RunRequest(BaseModel):
    target_url: str = "http://localhost:8000/demo"
    gemini_api_key: Optional[str] = None
    max_steps: int = 10
    safe_mode: bool = True
    storage_state_json: Optional[str] = None

async def broadcast_event(data: Dict[str, Any]):
    """Broadcasts a telemetry message to all connected WebSocket clients."""
    disconnected = []
    for ws in connected_websockets:
        try:
            await ws.send_json(data)
        except Exception:
            disconnected.append(ws)
    for ws in disconnected:
        if ws in connected_websockets:
            connected_websockets.remove(ws)

@app.get("/api/health")
async def health():
    return {
        "status": "healthy",
        "active_run": active_runner.is_running if active_runner else False
    }

@app.post("/api/run")
async def start_run(req: RunRequest, background_tasks: BackgroundTasks):
    global active_runner
    if active_runner and active_runner.is_running:
        raise HTTPException(status_code=400, detail="An exploration run is already in progress.")

    active_runner = AutonomousAgentRunner(
        target_url=req.target_url,
        gemini_api_key=req.gemini_api_key,
        max_steps=req.max_steps,
        safe_mode=req.safe_mode,
        storage_state_json=req.storage_state_json,
        on_event=broadcast_event
    )

    # Run agent in background
    background_tasks.add_task(active_runner.run)

    return {
        "status": "started",
        "target_url": req.target_url,
        "max_steps": req.max_steps,
        "safe_mode": req.safe_mode
    }

@app.post("/api/stop")
async def stop_run():
    global active_runner
    if active_runner and active_runner.is_running:
        active_runner.should_stop = True
        return {"status": "stopping"}
    return {"status": "idle"}

@app.get("/api/graph")
async def get_state_graph():
    if active_runner:
        return active_runner.graph.to_dict()
    return {"nodes": [], "edges": [], "current_node_id": None}

@app.get("/api/bugs")
async def get_bugs():
    if active_runner:
        return [b.to_dict() for b in active_runner.oracle.detected_bugs]
    return []

# Interactive Login Session Recorder Endpoints
class RecordStartRequest(BaseModel):
    url: str

@app.post("/api/auth/record-start")
async def record_start(req: RecordStartRequest, background_tasks: BackgroundTasks):
    if session_recorder.is_recording:
        await session_recorder.cancel()
    background_tasks.add_task(session_recorder.start, req.url)
    return {"status": "started", "url": req.url}

@app.post("/api/auth/record-finish")
async def record_finish():
    state = await session_recorder.finish()
    if state:
        return {"status": "captured", "storage_state": state}
    return {"status": "empty"}

@app.post("/api/auth/record-cancel")
async def record_cancel():
    await session_recorder.cancel()
    return {"status": "cancelled"}

@app.get("/api/auth/record-status")
async def record_status():
    return {
        "is_recording": session_recorder.is_recording,
        "has_captured": session_recorder.captured_state is not None,
        "storage_state": session_recorder.captured_state
    }

@app.websocket("/ws/run")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    connected_websockets.append(websocket)
    
    # Send current state snapshot immediately on connection
    if active_runner:
        initial_frame = {
            "type": "telemetry_frame",
            "step": len(active_runner.step_history),
            "max_steps": active_runner.max_steps,
            "current_action": "Connected to stream",
            "screenshot_b64": "",
            "graph": active_runner.graph.to_dict(),
            "bugs": [b.to_dict() for b in active_runner.oracle.detected_bugs],
            "total_bugs": len(active_runner.oracle.detected_bugs)
        }
        try:
            await websocket.send_json(initial_frame)
        except Exception:
            pass

    try:
        while True:
            data = await websocket.receive_text()
            try:
                msg = json.loads(data)
                if msg.get("type") == "stop" and active_runner:
                    active_runner.should_stop = True
            except Exception:
                pass
    except WebSocketDisconnect:
        if websocket in connected_websockets:
            connected_websockets.remove(websocket)
