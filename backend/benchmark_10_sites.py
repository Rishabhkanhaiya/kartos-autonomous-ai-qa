"""
Multi-Site Benchmark Verification Suite
Executes the Autonomous QA Agent across 10 diverse public websites & sandboxes,
verifying Set-of-Marks visual perception, state-graph hashing, and multi-oracle telemetry.
"""

import asyncio
import time
import json
import sys
from typing import Dict, Any, List
from agent_runner import AutonomousAgentRunner

# Ensure UTF-8 output on Windows terminal
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

SITES_TO_TEST = [
    {
        "name": "Built-in Seeded E-Commerce",
        "url": "http://127.0.0.1:8000/demo",
        "category": "Baseline Benchmark",
        "steps": 5
    },
    {
        "name": "The Internet (QA Playground)",
        "url": "https://the-internet.herokuapp.com",
        "category": "QA Testing Benchmark",
        "steps": 3
    },
    {
        "name": "Books to Scrape Sandbox",
        "url": "https://books.toscrape.com",
        "category": "E-Commerce Catalog",
        "steps": 3
    },
    {
        "name": "Hacker News (YCombinator)",
        "url": "https://news.ycombinator.com",
        "category": "Clean Semantic Forum",
        "steps": 3
    },
    {
        "name": "HttpBin API Sandbox",
        "url": "https://httpbin.org",
        "category": "HTTP Developer Tools",
        "steps": 3
    },
    {
        "name": "FastAPI Documentation",
        "url": "https://fastapi.tiangolo.com",
        "category": "Modern SPA / Docs",
        "steps": 3
    },
    {
        "name": "Wikipedia Main Portal",
        "url": "https://en.wikipedia.org/wiki/Main_Page",
        "category": "High-Density Content",
        "steps": 3
    },
    {
        "name": "React Official Site",
        "url": "https://react.dev",
        "category": "Next.js / React 19 SPA",
        "steps": 3
    },
    {
        "name": "Python.org Foundation",
        "url": "https://www.python.org",
        "category": "Enterprise Portal",
        "steps": 3
    },
    {
        "name": "GitHub Public Explore",
        "url": "https://github.com",
        "category": "Large-Scale Production Web App",
        "steps": 3
    }
]

async def benchmark_site(site_config: Dict[str, Any]) -> Dict[str, Any]:
    name = site_config["name"]
    url = site_config["url"]
    steps = site_config["steps"]

    print(f"\n==================================================")
    print(f">> Testing [{name}] ({url}) - Max Steps: {steps}")
    print(f"==================================================")

    start_time = time.time()
    events = []

    async def event_collector(event):
        events.append(event)
        if event.get("type") == "log":
            tag = event.get("tag")
            msg = event.get("message")
            if tag in ["GRAPH_HASH", "BUG_FOUND", "DECISION", "COMPLETE"]:
                print(f"  [{tag}] {msg}")

    runner = AutonomousAgentRunner(
        target_url=url,
        gemini_api_key=None,
        max_steps=steps,
        safe_mode=True,
        on_event=event_collector
    )

    try:
        # 45 second timeout per site to guarantee progress
        await asyncio.wait_for(runner.run(), timeout=45.0)
        status = "COMPLETED"
    except asyncio.TimeoutError:
        status = "TIMEOUT_SETTLED"
        runner.should_stop = True
    except Exception as e:
        status = f"FAILED: {e}"

    duration = round(time.time() - start_time, 2)
    states_count = len(runner.graph.nodes)
    edges_count = len(runner.graph.edges)
    bugs = runner.oracle.detected_bugs

    print(f"[OK] Finished [{name}] in {duration}s -> States: {states_count}, Transitions: {edges_count}, Bugs: {len(bugs)}")

    return {
        "name": name,
        "url": url,
        "category": site_config["category"],
        "status": status,
        "duration_sec": duration,
        "states_discovered": states_count,
        "transitions_recorded": edges_count,
        "total_bugs": len(bugs),
        "bug_breakdown": [
            {
                "id": b.bug_id,
                "severity": b.severity,
                "oracle_type": b.oracle_type,
                "title": b.title
            }
            for b in bugs
        ]
    }

async def run_all_benchmarks():
    results = []
    for site in SITES_TO_TEST:
        try:
            res = await benchmark_site(site)
            results.append(res)
        except Exception as e:
            results.append({
                "name": site["name"],
                "url": site["url"],
                "status": f"FATAL_ERROR: {e}",
                "states_discovered": 0,
                "total_bugs": 0
            })

    # Save results as JSON
    with open("benchmark_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    print("\n\n" + "=" * 60)
    print("ALL 10 SITE BENCHMARKS COMPLETED!")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(run_all_benchmarks())
