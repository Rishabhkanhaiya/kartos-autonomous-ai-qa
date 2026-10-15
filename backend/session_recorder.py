"""
Interactive Session Recorder for Playwright
Launches a visible Chromium window, injects a floating capture HUD,
and captures authenticated storageState (cookies & localStorage) after human login/2FA/CAPTCHA.
"""

import asyncio
from typing import Dict, Any, Optional
from playwright.async_api import async_playwright, Browser, BrowserContext, Page

FLOATING_RECORDER_HUD_JS = """
(() => {
    if (document.getElementById('kartos-recorder-hud')) return;

    const hud = document.createElement('div');
    hud.id = 'kartos-recorder-hud';
    hud.style.position = 'fixed';
    hud.style.top = '12px';
    hud.style.left = '50%';
    hud.style.transform = 'translateX(-50%)';
    hud.style.zIndex = '2147483647';
    hud.style.backgroundColor = '#090D16';
    hud.style.color = '#F1F5F9';
    hud.style.border = '2px solid #00F2FE';
    hud.style.boxShadow = '0 10px 30px rgba(0, 242, 254, 0.35)';
    hud.style.padding = '10px 18px';
    hud.style.borderRadius = '12px';
    hud.style.fontFamily = 'Inter, -apple-system, sans-serif';
    hud.style.fontSize = '13px';
    hud.style.display = 'flex';
    hud.style.alignItems = 'center';
    hud.style.gap = '14px';
    hud.style.userSelect = 'none';

    hud.innerHTML = `
        <div style="display:flex;align-items:center;gap:8px;">
            <span style="display:inline-block;width:10px;height:10px;border-radius:50%;background:#10B981;animation:pulse 1.5s infinite;"></span>
            <span style="font-weight:700;letter-spacing:0.5px;color:#00F2FE;">KARTOS RECORDER:</span>
            <span style="color:#CBD5E1;">Log in / solve 2FA, then click &rarr;</span>
        </div>
        <button id="btn-kartos-save-session" style="
            background: linear-gradient(135deg, #00F2FE, #10B981);
            color: #090D16;
            border: none;
            padding: 7px 16px;
            border-radius: 8px;
            font-weight: 800;
            font-size: 12px;
            cursor: pointer;
            box-shadow: 0 4px 12px rgba(0, 242, 254, 0.4);
            transition: transform 0.1s ease;
        ">
            ✓ Capture & Save Session
        </button>
    `;

    document.body.appendChild(hud);

    const btn = document.getElementById('btn-kartos-save-session');
    btn.onmouseover = () => { btn.style.transform = 'scale(1.05)'; };
    btn.onmouseout = () => { btn.style.transform = 'scale(1)'; };
    btn.onclick = () => {
        btn.innerText = 'Capturing...';
        btn.disabled = true;
        if (window.__kartosCaptureSession) {
            window.__kartosCaptureSession();
        }
    };
})()
"""

class InteractiveSessionRecorder:
    def __init__(self):
        self.is_recording = False
        self.captured_state: Optional[Dict[str, Any]] = None
        self._playwright = None
        self._browser: Optional[Browser] = None
        self._context: Optional[BrowserContext] = None
        self._page: Optional[Page] = None
        self._done_event = asyncio.Event()

    async def start(self, target_url: str) -> bool:
        """Launches a visible Chromium window for the user to log in."""
        if self.is_recording:
            await self.cancel()

        self.is_recording = True
        self.captured_state = None
        self._done_event.clear()

        try:
            self._playwright = await async_playwright().start()
            self._browser = await self._playwright.chromium.launch(
                headless=False,
                args=["--start-maximized", "--disable-blink-features=AutomationControlled"]
            )
            self._context = await self._browser.new_context(
                no_viewport=True,
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
            )
            self._page = await self._context.new_page()

            # Expose binding for the floating HUD button
            async def on_capture(source):
                await self.finish()

            await self._page.expose_binding("__kartosCaptureSession", on_capture)

            # Re-inject HUD bar on every page navigation / redirect
            async def on_load():
                try:
                    await self._page.evaluate(FLOATING_RECORDER_HUD_JS)
                except Exception:
                    pass

            self._page.on("load", lambda _: asyncio.create_task(on_load()))

            await self._page.goto(target_url, wait_until="domcontentloaded", timeout=30000)
            await on_load()
            return True
        except Exception as e:
            print(f"[SessionRecorder] Error starting recorder: {e}")
            await self.cancel()
            return False

    async def finish(self) -> Optional[Dict[str, Any]]:
        """Captures session state and safely closes the browser."""
        if not self.is_recording or not self._context:
            return None

        try:
            state = await self._context.storage_state()
            self.captured_state = state
            print(f"[SessionRecorder] Successfully captured session: {len(state.get('cookies', []))} cookies, {len(state.get('origins', []))} origins")
            self._done_event.set()
        except Exception as e:
            print(f"[SessionRecorder] Error capturing state: {e}")
        finally:
            await self._cleanup()

        return self.captured_state

    async def cancel(self):
        """Cancels recording and closes browser."""
        self.is_recording = False
        self._done_event.set()
        await self._cleanup()

    async def _cleanup(self):
        self.is_recording = False
        try:
            if self._browser:
                await self._browser.close()
            if self._playwright:
                await self._playwright.stop()
        except Exception:
            pass
        self._browser = None
        self._context = None
        self._page = None
        self._playwright = None

# Global singleton recorder instance
session_recorder = InteractiveSessionRecorder()
