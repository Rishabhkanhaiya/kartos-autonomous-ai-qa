"""
Built-in Seeded Buggy E-Commerce Application ('ApexPulse Audio & Tech')
Contains 4 deliberately seeded real-world bugs for deterministic multi-oracle detection.
"""

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
from typing import Optional

demo_router = APIRouter(prefix="/demo", tags=["Demo App"])

class CouponRequest(BaseModel):
    code: Optional[str] = ""

class SyncRequest(BaseModel):
    warehouse_id: Optional[str] = "WH-US-EAST"

# Seeded Bug 1: Empty coupon code triggers unhandled HTTP 500 error
@demo_router.post("/api/coupon/apply")
async def apply_coupon(req: CouponRequest):
    if not req.code or req.code.strip() == "":
        raise HTTPException(
            status_code=500,
            detail="Unhandled Database NullPointerException: coupon_code cannot be null at CheckoutSession.kt:142. Transaction aborted."
        )
    if req.code.upper() == "PROMO10":
        return {"discount": 10, "status": "applied", "message": "10% Discount applied!"}
    return {"discount": 0, "status": "invalid", "message": "Invalid coupon"}

# Seeded Bug 3: GraphQL / API endpoint that returns HTTP 200 but contains {"errors": [...]}
@demo_router.post("/api/inventory/sync")
@demo_router.post("/graphql")
async def inventory_sync(req: SyncRequest):
    return JSONResponse(
        status_code=200,
        content={
            "data": None,
            "errors": [
                {
                    "message": "Inventory sync failed: warehouse DB lock timeout on SKU-9942",
                    "code": "WAREHOUSE_DB_LOCK_TIMEOUT",
                    "path": ["mutation", "syncInventory"],
                    "locations": [{"line": 14, "column": 3}]
                }
            ],
            "extensions": {
                "traceId": "trace_99df738b021a",
                "timestamp": "2026-10-15T18:00:00Z"
            }
        }
    )

DEMO_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>ApexPulse Audio | High-End Studio Gear</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap" rel="stylesheet">
  <style>
    body { font-family: 'Plus Jakarta Sans', sans-serif; }
    /* Seeded Bug 4: Visual/Layout CSS Overlap bug */
    .mobile-overlap-badge {
      position: absolute;
      top: 10px;
      right: -10px;
      z-index: 50;
      transform: scale(0.95);
    }
  </style>
</head>
<body class="bg-slate-950 text-slate-100 min-h-screen">
  <!-- Top Navigation -->
  <header class="border-b border-slate-800 bg-slate-900/80 backdrop-blur sticky top-0 z-40">
    <div class="max-w-7xl mx-auto px-4 h-16 flex items-center justify-between">
      <div class="flex items-center gap-3">
        <div class="w-8 h-8 rounded-lg bg-cyan-500 flex items-center justify-center font-bold text-slate-950">A</div>
        <span class="font-extrabold text-lg tracking-wider text-white">APEXPULSE</span>
        <span class="text-xs font-mono bg-cyan-950 text-cyan-400 border border-cyan-800 px-2 py-0.5 rounded">DEMO STORE</span>
      </div>
      <div class="flex items-center gap-4">
        <button id="btn-sync-inventory" onclick="triggerInventorySync()" class="text-xs font-mono bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 px-3 py-1.5 rounded-md flex items-center gap-2">
          <span class="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
          Sync Warehouse
        </button>
        <button id="btn-open-cart" onclick="toggleCart(true)" class="relative bg-cyan-600 hover:bg-cyan-500 text-white font-medium px-4 py-2 rounded-lg text-sm flex items-center gap-2 transition">
          <span>Cart</span>
          <span id="cart-badge" class="bg-cyan-950 text-cyan-300 text-xs px-2 py-0.5 rounded-full font-bold">1</span>
        </button>
      </div>
    </div>
  </header>

  <!-- Main Storefront -->
  <main class="max-w-7xl mx-auto px-4 py-8">
    <div class="grid grid-cols-1 md:grid-cols-4 gap-8">
      <!-- Sidebar Filters -->
      <aside class="bg-slate-900 border border-slate-800 p-5 rounded-2xl h-fit">
        <h3 class="font-bold text-base mb-4 text-cyan-400">Audio Category</h3>
        <div class="space-y-2 mb-6 text-sm text-slate-300">
          <label class="flex items-center gap-2"><input type="checkbox" checked class="rounded border-slate-700"> Studio ANC</label>
          <label class="flex items-center gap-2"><input type="checkbox" class="rounded border-slate-700"> In-Ear Monitors</label>
          <label class="flex items-center gap-2"><input type="checkbox" class="rounded border-slate-700"> USB Condenser</label>
        </div>

        <h3 class="font-bold text-base mb-4 text-cyan-400">Price Tier</h3>
        <input type="range" class="w-full accent-cyan-400 mb-6" min="50" max="500">

        <!-- Seeded Bug 2: Silent TypeError in console -->
        <button id="btn-apply-filter" onclick="handleApplyFilter()" class="w-full bg-slate-800 hover:bg-slate-700 border border-slate-700 text-cyan-300 font-semibold py-2.5 rounded-xl text-sm transition">
          Apply Filter
        </button>
        <div id="filter-status" class="mt-2 text-xs text-slate-500 text-center font-mono">Ready</div>
      </aside>

      <!-- Products Grid -->
      <section class="md:col-span-3">
        <div class="flex items-center justify-between mb-6">
          <h2 class="text-xl font-bold">Featured High-Fidelity Gear</h2>
          <span class="text-xs text-slate-400 font-mono">Showing 3 of 12 items</span>
        </div>

        <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
          <!-- Product 1: Valid -->
          <div class="bg-slate-900 border border-slate-800 rounded-2xl p-4 flex flex-col justify-between hover:border-slate-700 transition">
            <div>
              <div class="h-44 bg-slate-800/80 rounded-xl mb-3 flex items-center justify-center overflow-hidden">
                <img src="https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=400&q=80" alt="Apex ANC Headphone" class="object-cover h-full w-full">
              </div>
              <span class="text-xs font-mono text-cyan-400 bg-cyan-950/60 px-2 py-0.5 rounded">NEW RELEASE</span>
              <h4 class="font-bold text-base mt-2">AuraPro Wireless ANC</h4>
              <p class="text-xs text-slate-400 mt-1">45mm custom planar drivers with active room calibration.</p>
            </div>
            <div class="mt-4 pt-3 border-t border-slate-800 flex items-center justify-between">
              <span class="font-extrabold text-lg">$299</span>
              <button id="btn-add-p1" onclick="addToCart('AuraPro Wireless ANC', 299)" class="bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-bold px-3 py-1.5 rounded-lg text-xs transition">
                Add to Cart
              </button>
            </div>
          </div>

          <!-- Product 2: Seeded Bug 4: Broken Image (naturalWidth === 0) -->
          <div class="bg-slate-900 border border-slate-800 rounded-2xl p-4 flex flex-col justify-between relative hover:border-slate-700 transition">
            <div>
              <div class="h-44 bg-slate-800/80 rounded-xl mb-3 flex items-center justify-center overflow-hidden border border-dashed border-rose-900/40">
                <!-- Broken image link deliberately seeded -->
                <img id="broken-product-img" src="/static/assets/non_existent_pulsebuds_v4_corrupted.png" alt="PulseBuds Studio Edition" class="object-contain max-h-full">
              </div>
              <span class="text-xs font-mono text-amber-400 bg-amber-950/60 px-2 py-0.5 rounded">LIMITED EDITION</span>
              <h4 class="font-bold text-base mt-2">PulseBuds Studio Ref</h4>
              <p class="text-xs text-slate-400 mt-1">Dual balanced armature drivers with low-latency Bluetooth 5.4.</p>
            </div>
            <div class="mt-4 pt-3 border-t border-slate-800 flex items-center justify-between">
              <span class="font-extrabold text-lg">$179</span>
              <button id="btn-add-p2" onclick="addToCart('PulseBuds Studio Ref', 179)" class="bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-bold px-3 py-1.5 rounded-lg text-xs transition">
                Add to Cart
              </button>
            </div>
          </div>

          <!-- Product 3: Valid -->
          <div class="bg-slate-900 border border-slate-800 rounded-2xl p-4 flex flex-col justify-between hover:border-slate-700 transition">
            <div>
              <div class="h-44 bg-slate-800/80 rounded-xl mb-3 flex items-center justify-center overflow-hidden">
                <img src="https://images.unsplash.com/photo-1590658268037-6bf12165a8df?w=400&q=80" alt="TitanStream Gaming Mic" class="object-cover h-full w-full">
              </div>
              <span class="text-xs font-mono text-purple-400 bg-purple-950/60 px-2 py-0.5 rounded">STUDIO PRO</span>
              <h4 class="font-bold text-base mt-2">TitanStream Condenser</h4>
              <p class="text-xs text-slate-400 mt-1">192kHz/24-bit cardioid pattern with analog gain limiter.</p>
            </div>
            <div class="mt-4 pt-3 border-t border-slate-800 flex items-center justify-between">
              <span class="font-extrabold text-lg">$149</span>
              <button id="btn-add-p3" onclick="addToCart('TitanStream Condenser', 149)" class="bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-bold px-3 py-1.5 rounded-lg text-xs transition">
                Add to Cart
              </button>
            </div>
          </div>
        </div>
      </section>
    </div>
  </main>

  <!-- Cart Drawer / Modal -->
  <div id="cart-drawer" class="fixed inset-0 bg-slate-950/80 backdrop-blur-sm z-50 hidden flex justify-end">
    <div class="bg-slate-900 border-l border-slate-800 w-full max-w-md h-full p-6 flex flex-col justify-between">
      <div>
        <div class="flex items-center justify-between pb-4 border-b border-slate-800">
          <h3 class="font-bold text-lg text-white">Your Checkout Bag</h3>
          <button id="btn-close-cart" onclick="toggleCart(false)" class="text-slate-400 hover:text-white text-xl font-bold">&times;</button>
        </div>

        <div class="py-4 space-y-3">
          <div class="flex items-center justify-between bg-slate-800/50 p-3 rounded-xl border border-slate-700">
            <div>
              <div class="font-semibold text-sm">AuraPro Wireless ANC</div>
              <div class="text-xs text-slate-400 font-mono">Qty: 1 &bull; Matte Black</div>
            </div>
            <span class="font-bold text-cyan-400">$299.00</span>
          </div>
        </div>

        <!-- Coupon Code Area -->
        <div class="mt-4 p-4 bg-slate-950/70 rounded-xl border border-slate-800">
          <label class="block text-xs font-semibold text-slate-300 mb-2">Promotional Voucher</label>
          <div class="flex gap-2">
            <input id="input-coupon" type="text" placeholder="e.g. PROMO10" class="bg-slate-900 border border-slate-700 text-sm px-3 py-2 rounded-lg w-full text-white placeholder-slate-500 focus:outline-none focus:border-cyan-500">
            <!-- Seeded Bug 1: Clicking Apply Coupon with empty string triggers 500 -->
            <button id="btn-apply-coupon" onclick="handleApplyCoupon()" class="bg-cyan-600 hover:bg-cyan-500 text-white font-bold text-xs px-4 py-2 rounded-lg transition whitespace-nowrap">
              Apply Code
            </button>
          </div>
          <div id="coupon-alert" class="mt-2 text-xs font-mono hidden"></div>
        </div>
      </div>

      <div class="pt-4 border-t border-slate-800">
        <div class="flex justify-between items-center mb-4">
          <span class="text-slate-400 text-sm">Order Total</span>
          <span class="text-xl font-extrabold text-white">$299.00</span>
        </div>
        <button id="btn-final-checkout" onclick="alert('Demo store checkout completed!')" class="w-full bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-bold py-3 rounded-xl transition">
          Confirm & Pay
        </button>
      </div>
    </div>
  </div>

  <script>
    function toggleCart(show) {
      const drawer = document.getElementById('cart-drawer');
      if (show) drawer.classList.remove('hidden');
      else drawer.classList.add('hidden');
    }

    function addToCart(title, price) {
      toggleCart(true);
    }

    // Seeded Bug 1 Handler: Empty coupon triggers unhandled 500 error
    async function handleApplyCoupon() {
      const code = document.getElementById('input-coupon').value;
      const alertBox = document.getElementById('coupon-alert');
      alertBox.className = 'mt-2 text-xs font-mono text-slate-400';
      alertBox.innerText = 'Validating coupon against checkout DB...';
      alertBox.classList.remove('hidden');

      try {
        const res = await fetch('/demo/api/coupon/apply', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ code: code })
        });
        if (!res.ok) {
          const err = await res.json();
          alertBox.className = 'mt-2 text-xs font-mono text-rose-400 bg-rose-950/40 p-2 rounded border border-rose-800';
          alertBox.innerText = 'HTTP 500 Crash: ' + (err.detail || 'Internal Server Error');
          return;
        }
        const data = await res.json();
        alertBox.className = 'mt-2 text-xs font-mono text-emerald-400';
        alertBox.innerText = data.message;
      } catch (e) {
        alertBox.className = 'mt-2 text-xs font-mono text-rose-400';
        alertBox.innerText = 'Network error: ' + e.message;
      }
    }

    // Seeded Bug 2 Handler: Silent TypeError
    function handleApplyFilter() {
      document.getElementById('filter-status').innerText = 'Filtering catalogue...';
      let unassignedConfig;
      // Triggers uncaught TypeError: Cannot read properties of undefined
      const category = unassignedConfig.category;
      console.log("Filter result:", category);
    }

    // Seeded Bug 3 Handler: GraphQL / REST 200 OK with silent "errors" key
    async function triggerInventorySync() {
      try {
        const res = await fetch('/demo/api/inventory/sync', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ warehouse_id: 'WH-US-EAST' })
        });
        const data = await res.json();
        console.log("Warehouse Sync Response (HTTP 200):", data);
      } catch (e) {
        console.error("Sync fetch error:", e);
      }
    }
  </script>
</body>
</html>
"""

@demo_router.get("", response_class=HTMLResponse)
@demo_router.get("/", response_class=HTMLResponse)
async def serve_demo_shop():
    return HTMLResponse(content=DEMO_HTML)
