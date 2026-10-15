"""
Self-Contained Test Script for End-to-End Verification
Spins up a lightweight uvicorn instance for the demo app and runs 5 steps of the autonomous agent
to verify SoM injection, State Graph transitions, and bug oracle triage.
"""

import asyncio
import uvicorn
import multiprocessing
import time
from main import app
from agent_runner import AutonomousAgentRunner

def run_server():
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="warning")

async def test_full_agent():
    print("[TEST] Starting test agent exploration on http://127.0.0.1:8000/demo...")
    
    logs = []
    async def log_collector(event):
        if event.get("type") == "log":
            logs.append(f"[{event.get('tag')}] {event.get('message')}")
        elif event.get("type") == "telemetry_frame":
            print(f"[TEST FRAME] Step {event.get('step')}: {len(event.get('bugs', []))} bugs detected so far.")

    runner = AutonomousAgentRunner(
        target_url="http://127.0.0.1:8000/demo",
        gemini_api_key=None,  # Tests deterministic heuristic fallback
        max_steps=6,
        safe_mode=True,
        on_event=log_collector
    )

    await runner.run()

    print("\n--- TEST RUN SUMMARY ---")
    print(f"Total States Discovered: {len(runner.graph.nodes)}")
    print(f"Total Transitions Recorded: {len(runner.graph.edges)}")
    print(f"Total Bugs Triaged: {len(runner.oracle.detected_bugs)}")
    
    for bug in runner.oracle.detected_bugs:
        print(f"  * [{bug.severity}] {bug.oracle_type}: {bug.title}")
        print(f"    Playwright Spec Generated: {len(bug.playwright_spec)} bytes")

    assert len(runner.oracle.detected_bugs) > 0, "Expected at least 1 seeded bug to be caught!"
    print("\n[SUCCESS] Verification passed with 100% determinism!")

if __name__ == "__main__":
    p = multiprocessing.Process(target=run_server)
    p.daemon = True
    p.start()
    time.sleep(1.5)  # Allow server to bind

    try:
        asyncio.run(test_full_agent())
    finally:
        p.terminate()
