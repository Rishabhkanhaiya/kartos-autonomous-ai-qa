"""
Set-of-Marks (SoM) Visual Grounding Injector
Injects high-contrast numbered mark badges and bounding boxes over all interactive DOM elements
for dual-modality visual grounding and coordinate-to-selector mapping.
"""

from typing import Dict, Any, List
from playwright.async_api import Page

SOM_INJECTION_JS = """
(() => {
    // 1. Remove any existing SoM overlay containers
    const existing = document.getElementById('som-overlay-container');
    if (existing) existing.remove();

    const container = document.createElement('div');
    container.id = 'som-overlay-container';
    container.style.position = 'fixed';
    container.style.top = '0';
    container.style.left = '0';
    container.style.width = '100vw';
    container.style.height = '100vh';
    container.style.pointerEvents = 'none';
    container.style.zIndex = '2147483647';
    document.body.appendChild(container);

    const interactiveSelectors = [
        'button',
        'a[href]',
        'input',
        'select',
        'textarea',
        '[role="button"]',
        '[role="link"]',
        '[role="menuitem"]',
        '[role="tab"]',
        '[role="checkbox"]',
        '[role="switch"]',
        '[onclick]',
        '[tabindex]:not([tabindex="-1"])',
        '.clickable',
        '.cursor-pointer'
    ];

    const elements = Array.from(document.querySelectorAll(interactiveSelectors.join(',')));
    const elementMap = {};
    let markId = 1;

    // Helper: generate robust CSS selector
    function getCssSelector(el) {
        if (el.id) return `#${CSS.escape(el.id)}`;
        if (el.getAttribute('data-testid')) return `[data-testid="${el.getAttribute('data-testid')}"]`;
        if (el.name) return `${el.tagName.toLowerCase()}[name="${el.name}"]`;
        
        let path = [];
        let curr = el;
        while (curr && curr.nodeType === Node.ELEMENT_NODE && curr !== document.body) {
            let selector = curr.tagName.toLowerCase();
            if (curr.className && typeof curr.className === 'string') {
                const classes = curr.className.trim().split(/\\s+/).filter(c => !c.startsWith('som-') && !c.includes(':') && c.length < 25);
                if (classes.length > 0) {
                    selector += '.' + classes.slice(0, 2).join('.');
                }
            }
            let sibling = curr;
            let nth = 1;
            while (sibling = sibling.previousElementSibling) {
                if (sibling.tagName === curr.tagName) nth++;
            }
            if (nth > 1) selector += `:nth-of-type(${nth})`;
            path.unshift(selector);
            curr = curr.parentElement;
            if (path.length > 4) break;
        }
        return path.join(' > ');
    }

    // Helper: generate XPath
    function getXPath(el) {
        if (el.id) return `//*[@id="${el.id}"]`;
        const parts = [];
        for (let curr = el; curr && curr.nodeType === Node.ELEMENT_NODE; curr = curr.parentNode) {
            let idx = 1;
            for (let sibling = curr.previousSibling; sibling; sibling = sibling.previousSibling) {
                if (sibling.nodeType === Node.ELEMENT_NODE && sibling.tagName === curr.tagName) idx++;
            }
            parts.unshift(`${curr.tagName.toLowerCase()}[${idx}]`);
            if (parts.length > 4) break;
        }
        return '/' + parts.join('/');
    }

    elements.forEach((el) => {
        // Check visibility and bounding box
        const rect = el.getBoundingClientRect();
        const style = window.getComputedStyle(el);

        if (
            rect.width <= 4 || 
            rect.height <= 4 || 
            style.visibility === 'hidden' || 
            style.display === 'none' || 
            parseFloat(style.opacity) < 0.1 ||
            rect.bottom <= 0 ||
            rect.right <= 0 ||
            rect.top >= window.innerHeight ||
            rect.left >= window.innerWidth
        ) {
            return;
        }

        // Avoid labeling container elements if they contain labeled interactive children
        const hasInteractiveChildren = el.querySelector(interactiveSelectors.join(','));
        if (hasInteractiveChildren && (el.tagName === 'DIV' || el.tagName === 'SECTION')) {
            return;
        }

        const id = markId++;
        const tag = el.tagName.toUpperCase();
        const text = (el.innerText || el.value || el.placeholder || el.getAttribute('aria-label') || el.title || '').trim().replace(/\\s+/g, ' ').slice(0, 60);
        const role = el.getAttribute('role') || (tag === 'BUTTON' ? 'button' : tag === 'A' ? 'link' : tag === 'INPUT' ? 'input' : 'generic');
        const ariaLabel = el.getAttribute('aria-label') || '';
        const inputType = el.getAttribute('type') || '';
        const placeholder = el.getAttribute('placeholder') || '';
        const selector = getCssSelector(el);
        const xpath = getXPath(el);

        // Render bounding box
        const box = document.createElement('div');
        box.className = 'som-box';
        box.style.position = 'absolute';
        box.style.left = `${window.scrollX + rect.left}px`;
        box.style.top = `${window.scrollY + rect.top}px`;
        box.style.width = `${rect.width}px`;
        box.style.height = `${rect.height}px`;
        box.style.border = '2px solid #00F2FE';
        box.style.boxShadow = '0 0 6px rgba(0, 242, 254, 0.4)';
        box.style.borderRadius = '3px';
        box.style.pointerEvents = 'none';

        // Render badge
        const badge = document.createElement('div');
        badge.className = 'som-badge';
        badge.innerText = `[${id}]`;
        badge.style.position = 'absolute';
        badge.style.left = `${Math.max(0, window.scrollX + rect.left - 2)}px`;
        badge.style.top = `${Math.max(0, window.scrollY + rect.top - 18)}px`;
        badge.style.backgroundColor = '#00F2FE';
        badge.style.color = '#090D16';
        badge.style.fontFamily = 'monospace';
        badge.style.fontSize = '11px';
        badge.style.fontWeight = '800';
        badge.style.padding = '1px 4px';
        badge.style.borderRadius = '3px';
        badge.style.zIndex = '2147483647';
        badge.style.boxShadow = '0 2px 4px rgba(0,0,0,0.6)';

        container.appendChild(box);
        container.appendChild(badge);

        elementMap[id] = {
            mark_id: id,
            tag: tag,
            text: text,
            role: role,
            aria_label: ariaLabel,
            input_type: inputType,
            placeholder: placeholder,
            selector: selector,
            xpath: xpath,
            bbox: {
                x: Math.round(rect.left),
                y: Math.round(rect.top),
                width: Math.round(rect.width),
                height: Math.round(rect.height)
            }
        };
    });

    return elementMap;
})()
"""

SOM_CLEANUP_JS = """
(() => {
    const existing = document.getElementById('som-overlay-container');
    if (existing) existing.remove();
    return true;
})()
"""

class SoMInjector:
    """Manages injection of Set-of-Marks visual overlay badges into a target Playwright page."""

    @staticmethod
    async def inject(page: Page) -> Dict[str, Any]:
        """
        Injects numbered badges over interactive elements and returns element metadata map.
        """
        try:
            element_map = await page.evaluate(SOM_INJECTION_JS)
            return element_map or {}
        except Exception as e:
            print(f"[SoMInjector] Error injecting SoM: {e}")
            return {}

    @staticmethod
    async def cleanup(page: Page) -> bool:
        """
        Removes all Set-of-Marks overlay DOM elements.
        """
        try:
            await page.evaluate(SOM_CLEANUP_JS)
            return True
        except Exception as e:
            print(f"[SoMInjector] Error cleaning up SoM: {e}")
            return False
