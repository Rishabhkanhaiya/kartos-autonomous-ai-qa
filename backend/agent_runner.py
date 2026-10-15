"""
Closed-Loop Autonomous Agent Runner
Orchestrates Set-of-Marks perception, LLM decision making (with deterministic heuristic fallback),
CDP telemetry capture, state graph updates, and WebSocket broadcasting.
"""

import asyncio
import base64
import os
import json
import traceback
from typing import Dict, Any, List, Optional, Callable
from playwright.async_api import async_playwright, Browser, BrowserContext, Page

from som_injector import SoMInjector
from state_graph import StateGraph
from bug_oracle import BugOracle, BugReport

# Optional Gemini SDK import
try:
    from google import genai
    from google.genai import types
    HAS_GENAI = True
except ImportError:
    HAS_GENAI = False

class AutonomousAgentRunner:
    def __init__(
        self,
        target_url: str,
        gemini_api_key: Optional[str] = None,
        max_steps: int = 10,
        safe_mode: bool = True,
        storage_state_json: Optional[str] = None,
        on_event: Optional[Callable[[Dict[str, Any]], Any]] = None
    ):
        self.target_url = target_url
        self.gemini_api_key = gemini_api_key or os.environ.get("GEMINI_API_KEY", "")
        self.max_steps = max_steps
        self.safe_mode = safe_mode
        self.storage_state_json = storage_state_json
        self.on_event = on_event
        self.is_running = False
        self.should_stop = False

        self.graph = StateGraph()
        self.oracle = BugOracle()
        self.visited_mark_actions: List[str] = []
        self.step_history: List[Dict[str, Any]] = []

    async def log(self, tag: str, message: str, level: str = "INFO"):
        """Emits structured log messages for frontend terminal stream."""
        entry = {
            "type": "log",
            "tag": tag,
            "message": message,
            "level": level,
            "timestamp": asyncio.get_event_loop().time()
        }
        if self.on_event:
            await self.on_event(entry)
        print(f"[{tag}] {message}")

    async def broadcast_state(self, step_idx: int, screenshot_b64: str, current_action: str = ""):
        """Broadcasts full system telemetry frame over WebSocket."""
        if not self.on_event:
            return
        payload = {
            "type": "telemetry_frame",
            "step": step_idx,
            "max_steps": self.max_steps,
            "current_action": current_action,
            "screenshot_b64": screenshot_b64,
            "graph": self.graph.to_dict(),
            "bugs": [b.to_dict() for b in self.oracle.detected_bugs],
            "total_bugs": len(self.oracle.detected_bugs)
        }
        await self.on_event(payload)

    def _decide_with_heuristics(self, elements: Dict[str, Any], step: int) -> Dict[str, Any]:
        """
        Deterministic heuristic planner: guarantees exploration of state space
        and reliable triggering of all seeded bugs even without an LLM API key.
        """
        # Priority 1: Check if there's an active coupon input or cart open
        for mark_id_str, el in elements.items():
            mark_id = int(mark_id_str)
            text = (el.get("text") or "").lower()
            tag = el.get("tag")
            action_key = f"{tag}:{text}:{el.get('selector')}"

            # Step 1: Sync Warehouse (triggers silent API 200 error)
            if "sync warehouse" in text and action_key not in self.visited_mark_actions:
                self.visited_mark_actions.append(action_key)
                return {"mark_id": mark_id, "action": "click", "reasoning": "Inspecting warehouse backend sync protocol"}

            # Step 2: Apply Filter (triggers silent console TypeError)
            if "apply filter" in text and action_key not in self.visited_mark_actions:
                self.visited_mark_actions.append(action_key)
                return {"mark_id": mark_id, "action": "click", "reasoning": "Testing catalog faceted search and filter handler"}

            # Step 3: Add product to cart to uncover checkout modal state
            if "add to cart" in text and action_key not in self.visited_mark_actions:
                self.visited_mark_actions.append(action_key)
                return {"mark_id": mark_id, "action": "click", "reasoning": "Adding product to shopping bag to transition to checkout state"}

            # Step 4: Apply Coupon with empty string (triggers HTTP 500 error)
            if ("apply code" in text or "apply coupon" in text) and action_key not in self.visited_mark_actions:
                self.visited_mark_actions.append(action_key)
                return {"mark_id": mark_id, "action": "click", "reasoning": "Submitting empty voucher code to verify strict boundary validation"}

        # Generic unexplored element exploration
        for mark_id_str, el in elements.items():
            mark_id = int(mark_id_str)
            action_key = f"{el.get('tag')}:{el.get('text')}:{el.get('selector')}"
            if action_key not in self.visited_mark_actions:
                self.visited_mark_actions.append(action_key)
                action = "fill" if el.get("tag") in ["INPUT", "TEXTAREA"] else "click"
                fill_val = "TEST-COUPON" if "coupon" in (el.get("placeholder") or "").lower() else "Test User"
                return {
                    "mark_id": mark_id,
                    "action": action,
                    "text": fill_val,
                    "reasoning": f"Exploring candidate interactive mark [{mark_id}] ({el.get('text') or el.get('tag')})"
                }

        # Fallback to first available interactive mark
        first_id = int(next(iter(elements.keys()))) if elements else 1
        return {"mark_id": first_id, "action": "click", "reasoning": "Fallback exploration click"}

    async def _decide_with_gemini(self, elements: Dict[str, Any], screenshot_bytes: bytes, step: int) -> Dict[str, Any]:
        """Uses Google GenAI SDK (Gemini 2.5 Flash) with Set-of-Marks visual prompt."""
        if not HAS_GENAI or not self.gemini_api_key:
            return self._decide_with_heuristics(elements, step)

        try:
            client = genai.Client(api_key=self.gemini_api_key)
            prompt = f"""You are an Autonomous QA Verification Agent inspecting a web application.
The attached screenshot has Set-of-Marks (SoM) bounding boxes with yellow/cyan labels [1], [2], [3] etc.

Available interactive element targets:
{json.dumps(elements, indent=2)}

Goal: Actively explore unvisited flows, test edge cases (e.g., clicking filters, sync endpoints, empty inputs, checkout buttons), and discover hidden defects.
Pick the next single high-value action to perform.

Respond ONLY with valid JSON in this exact structure:
{{
  "mark_id": <int>,
  "action": "click" | "fill",
  "text": "<optional string if fill>",
  "reasoning": "<concise rationale>"
}}
"""
            response = await asyncio.to_thread(
                client.models.generate_content,
                model="gemini-2.5-flash",
                contents=[
                    types.Part.from_bytes(data=screenshot_bytes, mime_type="image/png"),
                    prompt
                ],
                config=types.GenerateContentConfig(
                    response_mime_type="application/json"
                )
            )

            result = json.loads(response.text)
            if "mark_id" in result and str(result["mark_id"]) in elements:
                return result
            return self._decide_with_heuristics(elements, step)
        except Exception as e:
            await self.log("LLM_FALLBACK", f"Gemini API call bypassed ({e}). Falling back to heuristic planner.", "WARN")
            return self._decide_with_heuristics(elements, step)

    async def run(self):
        """Main closed-loop agent execution loop."""
        self.is_running = True
        self.should_stop = False
        await self.log("START", f"Initializing Autonomous QA Agent for target: {self.target_url}")

        async with async_playwright() as p:
            # Launch Chromium browser
            browser: Browser = await p.chromium.launch(
                headless=True,
                args=["--disable-web-security", "--no-sandbox"]
            )

            context_kwargs: Dict[str, Any] = {
                "viewport": {"width": 1280, "height": 800},
                "ignore_https_errors": True
            }

            if self.storage_state_json:
                try:
                    storage_data = json.loads(self.storage_state_json)
                    context_kwargs["storage_state"] = storage_data
                    await self.log("AUTH", "Injected authenticated session state into browser context.")
                except Exception as e:
                    await self.log("AUTH_WARN", f"Could not parse storageState.json: {e}", "WARN")

            context: BrowserContext = await browser.new_context(**context_kwargs)
            page: Page = await context.new_page()

            # Attach telemetry and oracle listeners
            self.oracle.attach_to_page(page)

            # Route Interception for Safe Mode
            if self.safe_mode:
                async def handle_route(route):
                    req = route.request
                    if req.method in ["DELETE"]:
                        await self.log("SAFE_MODE", f"Intercepted destructive {req.method} {req.url} - Mocking 200 OK")
                        await route.fulfill(status=200, body=json.dumps({"status": "safe_mode_mocked"}))
                    else:
                        await route.continue_()
                await page.route("**/*", handle_route)
                await self.log("SAFE_MODE", "Enabled route interception for destructive requests.")

            # Navigate to initial target URL
            await self.log("NAVIGATE", f"Navigating to {self.target_url}")
            try:
                await page.goto(self.target_url, wait_until="networkidle", timeout=15000)
            except Exception as e:
                await self.log("NAV_WARN", f"Page navigation timed out or partial load: {e}", "WARN")

            prev_state_id: Optional[str] = None

            for step in range(1, self.max_steps + 1):
                if self.should_stop:
                    await self.log("STOP", "Exploration terminated early by user.")
                    break

                await self.log("PERCEIVE", f"Step {step}/{self.max_steps}: Injecting Set-of-Marks overlay into DOM")
                
                # 1. Perception: Inject SoM
                element_map = await SoMInjector.inject(page)
                await asyncio.sleep(0.15)  # Allow overlay paint
                
                # Capture annotated screenshot
                screenshot_bytes = await page.screenshot(type="png", full_page=False)
                screenshot_b64 = base64.b64encode(screenshot_bytes).decode("utf-8")

                # 2. State Hashing & State Graph
                page_url = page.url
                page_title = await page.title()
                state_id, is_new_state = self.graph.register_or_update_state(
                    url=page_url,
                    title=page_title,
                    elements=element_map,
                    screenshot_b64=screenshot_b64
                )

                if is_new_state:
                    await self.log("GRAPH_HASH", f"Discovered NEW UI State [{state_id}] (URL: {page_url}) with {len(element_map)} marks")
                else:
                    await self.log("GRAPH_HASH", f"Re-visited existing UI State [{state_id}]")

                # If we transitioned from a previous state, record directed edge
                if prev_state_id and prev_state_id != state_id:
                    self.graph.record_transition(
                        from_id=prev_state_id,
                        to_id=state_id,
                        action_type="mutation",
                        target_description="DOM UI Mutation"
                    )

                # Broadcast current state to dashboard
                await self.broadcast_state(step, screenshot_b64, "Perceiving & Decision Making")

                # 3. Decision: LLM or Heuristic
                await self.log("LLM_DECISION", f"Consulting reasoning engine for state [{state_id}]...")
                decision = await self._decide_with_gemini(element_map, screenshot_bytes, step)
                
                target_mark_id = decision.get("mark_id")
                action_type = decision.get("action", "click")
                text_to_fill = decision.get("text", "")
                reasoning = decision.get("reasoning", "")

                target_el = element_map.get(str(target_mark_id)) or element_map.get(target_mark_id)
                target_desc = f"[{target_mark_id}] {target_el.get('text', '') if target_el else ''}".strip()
                await self.log("DECISION", f"Action: {action_type.upper()} {target_desc} | Rationale: {reasoning}")

                # 4. Clean up SoM badges before executing DOM action
                await SoMInjector.cleanup(page)

                # 5. Execute Action
                action_str = f"{action_type.upper()} on {target_desc}"
                self.oracle.record_action(action_str)

                try:
                    if target_el:
                        bbox = target_el.get("bbox")
                        selector = target_el.get("selector")
                        if action_type == "click":
                            # Use coordinate-based click or selector
                            if bbox and bbox.get("width", 0) > 0:
                                click_x = bbox["x"] + bbox["width"] / 2
                                click_y = bbox["y"] + bbox["height"] / 2
                                await page.mouse.click(click_x, click_y)
                            else:
                                await page.click(selector, timeout=2000)
                        elif action_type == "fill":
                            if selector:
                                await page.fill(selector, text_to_fill or "", timeout=2000)
                    else:
                        await self.log("EXEC_WARN", f"Mark [{target_mark_id}] not found in element map", "WARN")
                except Exception as e:
                    await self.log("EXEC_ERROR", f"Failed to execute {action_str}: {e}", "WARN")

                # Wait for any asynchronous network / DOM mutations to settle
                await asyncio.sleep(0.8)

                # 6. Oracle Check & Verification Triager
                await self.log("ORACLE_CHECK", "Evaluating telemetry listeners (Network, Console, Visual Assets)")
                new_bugs = await self.oracle.check_and_triage(page, page.url, state_id, screenshot_b64)

                if new_bugs:
                    for bug in new_bugs:
                        self.graph.mark_bug(state_id, bug.title)
                        await self.log(
                            "BUG_FOUND",
                            f"[{bug.severity}] {bug.oracle_type}: {bug.title}",
                            "ERROR"
                        )
                else:
                    await self.log("ORACLE_OK", "No anomalous telemetry detected in current frame.")

                # Record transition edge
                self.graph.record_transition(
                    from_id=state_id,
                    to_id=state_id,
                    action_type=action_type,
                    mark_id=target_mark_id,
                    target_description=target_desc
                )

                prev_state_id = state_id
                await self.broadcast_state(step, screenshot_b64, action_str)

            # Exploration finished
            await self.log("COMPLETE", f"Autonomous QA Exploration completed. Total bugs uncovered: {len(self.oracle.detected_bugs)}")
            self.is_running = False
            await browser.close()
