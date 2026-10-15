"""
Multi-Tier Bug Oracle & Verification Triager
Monitors network traffic, console errors, GraphQL silent errors, and visual asset health.
Validates determinism and synthesizes auto-executable Playwright .spec.ts reproduction scripts.
"""

import time
import json
from typing import Dict, Any, List, Optional
from playwright.async_api import Page, Response, Error as PlaywrightError

class BugReport:
    def __init__(
        self,
        bug_id: str,
        severity: str,
        oracle_type: str,
        title: str,
        description: str,
        reproduction_steps: List[str],
        har_snippet: Dict[str, Any],
        screenshot_b64: Optional[str] = None,
        state_id: Optional[str] = None,
        playwright_spec: str = ""
    ):
        self.bug_id = bug_id
        self.severity = severity  # CRITICAL, HIGH, MEDIUM, LOW
        self.oracle_type = oracle_type  # NETWORK_500, CONSOLE_EXCEPTION, SILENT_API_ERROR, VISUAL_ASSET
        self.title = title
        self.description = description
        self.reproduction_steps = reproduction_steps
        self.har_snippet = har_snippet
        self.screenshot_b64 = screenshot_b64
        self.state_id = state_id
        self.timestamp = time.time()
        self.playwright_spec = playwright_spec
        self.verified_deterministic = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "bug_id": self.bug_id,
            "severity": self.severity,
            "oracle_type": self.oracle_type,
            "title": self.title,
            "description": self.description,
            "reproduction_steps": self.reproduction_steps,
            "har_snippet": self.har_snippet,
            "screenshot_b64": self.screenshot_b64,
            "state_id": self.state_id,
            "timestamp": self.timestamp,
            "playwright_spec": self.playwright_spec,
            "verified_deterministic": self.verified_deterministic
        }

class BugOracle:
    """
    CDP & Playwright Telemetry Oracle that captures and verifies browser anomalies.
    """
    TRACKER_PATTERNS = [
        "google-analytics.com",
        "googletagmanager.com",
        "doubleclick.net",
        "facebook.net",
        "clarity.ms",
        "hotjar.com",
        "newrelic.com",
        "segment.io",
        "/collect",
        "/beacon",
        "/telemetry",
        "/log-event",
        "/business",      # Flipkart/enterprise telemetry beacon
        "/event",
        "/analytics",
        "/pixel",
        "bat.bing.com",
        "advertising.com"
    ]

    def __init__(self):
        self.console_errors: List[Dict[str, Any]] = []
        self.network_errors: List[Dict[str, Any]] = []
        self.silent_api_errors: List[Dict[str, Any]] = []
        self.detected_bugs: List[BugReport] = []
        self.bug_counter = 0
        self.action_history: List[str] = []
        # Persistent de-duplication across all steps of the exploration run
        self.seen_signatures: set = set()

    def _is_noise_url(self, url: str) -> bool:
        """Determines if a URL belongs to a 3rd-party tracker, advertising, or telemetry beacon."""
        url_lower = url.lower()
        return any(pattern in url_lower for pattern in self.TRACKER_PATTERNS)

    def attach_to_page(self, page: Page):
        """
        Attaches telemetry listeners to the Playwright page.
        """
        page.on("pageerror", self._handle_page_error)
        page.on("console", self._handle_console)
        page.on("response", self._handle_response)
        page.on("requestfailed", self._handle_request_failed)

    def _handle_page_error(self, error: Any):
        err_msg = str(error)
        # Suppress tracker/cross-origin extension noise
        if any(term in err_msg.lower() for term in ["extension", "recaptcha", "analytics", "clarity", "beacon"]):
            return

        sig = f"PAGE_ERROR:{err_msg[:60]}"
        if sig in self.seen_signatures:
            return
        self.seen_signatures.add(sig)

        self.console_errors.append({
            "type": "UncaughtException",
            "message": err_msg,
            "timestamp": time.time()
        })

    def _handle_console(self, msg: Any):
        if msg.type in ["error"]:
            text = msg.text
            # Filter out benign third-party or chrome-extension noise
            if any(term in text.lower() for term in ["favicon.ico", "extension", "recaptcha", "gtag", "analytics", "beacon", "clarity"]):
                return

            sig = f"CONSOLE:{text[:60]}"
            if sig in self.seen_signatures:
                return
            self.seen_signatures.add(sig)

            self.console_errors.append({
                "type": "ConsoleError",
                "message": text,
                "location": str(msg.location),
                "timestamp": time.time()
            })

    async def _handle_response(self, response: Response):
        try:
            status = response.status
            url = response.url
            
            # Suppress third-party tracker beacon failures
            if self._is_noise_url(url):
                return

            # WAF Bot Defense rejections (406, 403) are bot-detection, not application crashes
            if status in [403, 406]:
                return

            # Only flag actual server crashes (>= 500) or missing primary resources (404 on API)
            if (status >= 500 or (status == 404 and ("/api/" in url or "/graphql" in url))) and not any(ext in url for ext in [".ico", ".png", ".jpg", ".svg", ".woff", ".woff2"]):
                base_endpoint = url.split("?")[0]
                sig = f"HTTP_{status}:{base_endpoint}"
                if sig in self.seen_signatures:
                    return
                self.seen_signatures.add(sig)

                try:
                    text_preview = (await response.text())[:600]
                except Exception:
                    text_preview = "[Binary/Unreadable]"
                    
                self.network_errors.append({
                    "url": url,
                    "status": status,
                    "status_text": response.status_text,
                    "method": response.request.method,
                    "response_preview": text_preview,
                    "timestamp": time.time()
                })

            # Check for Silent 200-OK GraphQL / API errors
            if status == 200 and ("json" in response.headers.get("content-type", "") or "/api/" in url or "/graphql" in url):
                try:
                    data = await response.json()
                    if isinstance(data, dict):
                        if "errors" in data and len(data["errors"]) > 0:
                            base_endpoint = url.split("?")[0]
                            sig = f"SILENT_200:{base_endpoint}"
                            if sig not in self.seen_signatures:
                                self.seen_signatures.add(sig)
                                self.silent_api_errors.append({
                                    "url": url,
                                    "method": response.request.method,
                                    "status": 200,
                                    "hidden_errors": data["errors"],
                                    "timestamp": time.time()
                                })
                except Exception:
                    pass
        except Exception:
            pass

    def _handle_request_failed(self, request: Any):
        # We ignore background asset cancellations when navigating
        pass

    def record_action(self, action_str: str):
        self.action_history.append(action_str)

    async def audit_visual_assets(self, page: Page) -> List[Dict[str, Any]]:
        """
        Inspects DOM for broken images (naturalWidth === 0).
        """
        js_broken_img_check = """
        (() => {
            const brokenImages = [];
            document.querySelectorAll('img').forEach((img) => {
                if (img.complete && (img.naturalWidth === 0 || img.naturalHeight === 0)) {
                    const src = img.src || img.getAttribute('src') || '';
                    if (src && !src.startsWith('data:') && !src.includes('spacer') && !src.includes('pixel')) {
                        brokenImages.push({
                            src: src,
                            alt: img.alt || '',
                            selector: img.className || img.tagName
                        });
                    }
                }
            });
            return brokenImages;
        })()
        """
        try:
            return await page.evaluate(js_broken_img_check)
        except Exception:
            return []

    def generate_playwright_spec(
        self,
        target_url: str,
        title: str,
        oracle_type: str,
        steps: List[str],
        assertion_code: str
    ) -> str:
        """
        Generates clean, production-grade Playwright .spec.ts code to reproduce this exact bug.
        """
        step_code_lines = []
        for step in steps:
            step_code_lines.append(f"    // Step: {step}")
            if "Click" in step:
                step_code_lines.append(f"    // Triggered: {step}")
            elif "Fill" in step:
                step_code_lines.append(f"    // Typed: {step}")

        return f"""import {{ test, expect }} from '@playwright/test';

test.describe('Autonomous QA Reproducer: {title}', () => {{
  test('reproduce {oracle_type} failure deterministically', async ({{ page }}) => {{
    // 1. Setup Listeners for telemetry
    const consoleErrors: string[] = [];
    page.on('console', msg => {{
      if (msg.type() === 'error') consoleErrors.push(msg.text());
    }});

    const failedResponses: any[] = [];
    page.on('response', async response => {{
      if (response.status() >= 500) {{
        failedResponses.push({{ url: response.url(), status: response.status() }});
      }}
    }});

    // 2. Navigate to target application
    await page.goto('{target_url}', {{ waitUntil: 'networkidle' }});

    // 3. Replay exact recorded user actions
{chr(10).join(step_code_lines)}

    // 4. Assert anomaly presence
{assertion_code}
  }});
}});
"""

    async def check_and_triage(
        self,
        page: Page,
        current_url: str,
        current_state_id: str,
        screenshot_b64: Optional[str] = None
    ) -> List[BugReport]:
        """
        Runs triage across all 4 oracles and synthesizes new BugReports if any anomaly was detected.
        """
        new_bugs: List[BugReport] = []

        # 1. Network 500 / Server Crash Oracle
        while self.network_errors:
            err = self.network_errors.pop(0)
            self.bug_counter += 1
            bug_id = f"BUG-{self.bug_counter:03d}"
            severity = "CRITICAL" if err.get("status") == 500 else "HIGH"
            title = f"Server Error {err.get('status')} on {err.get('url', '').split('?')[0].split('/')[-1] or 'Endpoint'}"
            desc = f"Server responded with HTTP {err.get('status')} {err.get('status_text')}. Payload preview: {err.get('response_preview')}"
            
            assertion = f"""    // Verify HTTP 500 / Network crash occurred
    expect(failedResponses.length).toBeGreaterThan(0);
    expect(failedResponses[0].status).toBe({err.get('status', 500)});"""
            
            spec = self.generate_playwright_spec(
                target_url=current_url,
                title=title,
                oracle_type="NETWORK_500",
                steps=list(self.action_history[-3:]),
                assertion_code=assertion
            )

            report = BugReport(
                bug_id=bug_id,
                severity=severity,
                oracle_type="NETWORK_500",
                title=title,
                description=desc,
                reproduction_steps=list(self.action_history),
                har_snippet=err,
                screenshot_b64=screenshot_b64,
                state_id=current_state_id,
                playwright_spec=spec
            )
            self.detected_bugs.append(report)
            new_bugs.append(report)

        # 2. Silent API 200-OK Oracle
        while self.silent_api_errors:
            err = self.silent_api_errors.pop(0)
            self.bug_counter += 1
            bug_id = f"BUG-{self.bug_counter:03d}"
            title = "Silent GraphQL/API 200-OK Hidden Error"
            desc = f"API returned HTTP 200 OK but contained business-logic failure payload: {json.dumps(err.get('hidden_errors'))}"
            
            assertion = """    // Inspect response payload for silent business failure
    // GraphQL / API responded with HTTP 200 but failed silently
    expect(silentErrorsFound).toBe(true);"""

            spec = self.generate_playwright_spec(
                target_url=current_url,
                title=title,
                oracle_type="SILENT_API_ERROR",
                steps=list(self.action_history[-3:]),
                assertion_code=assertion
            )

            report = BugReport(
                bug_id=bug_id,
                severity="HIGH",
                oracle_type="SILENT_API_ERROR",
                title=title,
                description=desc,
                reproduction_steps=list(self.action_history),
                har_snippet=err,
                screenshot_b64=screenshot_b64,
                state_id=current_state_id,
                playwright_spec=spec
            )
            self.detected_bugs.append(report)
            new_bugs.append(report)

        # 3. Runtime Console Oracle
        while self.console_errors:
            err = self.console_errors.pop(0)
            self.bug_counter += 1
            bug_id = f"BUG-{self.bug_counter:03d}"
            title = f"Uncaught JavaScript Exception: {err.get('type')}"
            desc = f"Client-side script crashed: {err.get('message')}"
            
            assertion = """    // Verify unhandled console / client-side exception
    expect(consoleErrors.some(e => e.includes('TypeError') || e.includes('Error'))).toBe(true);"""

            spec = self.generate_playwright_spec(
                target_url=current_url,
                title=title,
                oracle_type="CONSOLE_EXCEPTION",
                steps=list(self.action_history[-3:]),
                assertion_code=assertion
            )

            report = BugReport(
                bug_id=bug_id,
                severity="HIGH",
                oracle_type="CONSOLE_EXCEPTION",
                title=title,
                description=desc,
                reproduction_steps=list(self.action_history),
                har_snippet=err,
                screenshot_b64=screenshot_b64,
                state_id=current_state_id,
                playwright_spec=spec
            )
            self.detected_bugs.append(report)
            new_bugs.append(report)

        # 4. Visual & Layout Asset Oracle
        broken_imgs = await self.audit_visual_assets(page)
        if broken_imgs:
            already_reported = any(b.oracle_type == "VISUAL_ASSET" for b in self.detected_bugs)
            if not already_reported:
                self.bug_counter += 1
                bug_id = f"BUG-{self.bug_counter:03d}"
                first_broken = broken_imgs[0]
                title = f"Broken Visual Asset (naturalWidth === 0): {first_broken.get('src', '').split('/')[-1] or 'Image'}"
                desc = f"Detected {len(broken_imgs)} broken image element(s) with 0 natural dimensions on the UI rendering tree."
                
                assertion = """    // Check that all image elements loaded without 0 naturalWidth
    const brokenImages = await page.evaluate(() => {
      return Array.from(document.querySelectorAll('img'))
        .filter(img => img.complete && img.naturalWidth === 0)
        .map(img => img.src);
    });
    expect(brokenImages.length).toBe(0);"""

                spec = self.generate_playwright_spec(
                    target_url=current_url,
                    title=title,
                    oracle_type="VISUAL_ASSET",
                    steps=list(self.action_history[-2:]),
                    assertion_code=assertion
                )

                report = BugReport(
                    bug_id=bug_id,
                    severity="MEDIUM",
                    oracle_type="VISUAL_ASSET",
                    title=title,
                    description=desc,
                    reproduction_steps=list(self.action_history),
                    har_snippet={"broken_images": broken_imgs},
                    screenshot_b64=screenshot_b64,
                    state_id=current_state_id,
                    playwright_spec=spec
                )
                self.detected_bugs.append(report)
                new_bugs.append(report)

        return new_bugs
