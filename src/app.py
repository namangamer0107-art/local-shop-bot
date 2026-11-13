import json
import logging
from typing import Optional
from fastapi import FastAPI, Request, Query, Response, HTTPException, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from src.config import settings
from src.services.whatsapp import WhatsAppService
from src.services.tenant_manager import tenant_manager
from src.services.conversation_flow import ConversationFlow
from src.services.broadcast import BroadcastService
from src.services.database import db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("local_bot")

app = FastAPI(
    title="Local Shop WhatsApp Bot Agency Platform",
    description="Multi-tenant agency portal with Super Admin controls and Shopkeeper self-service.",
    version="3.0.0",
)

whatsapp_service = WhatsAppService()
broadcast_service = BroadcastService(whatsapp_service)

ADMIN_USER = "naman"
ADMIN_PASS = "balleballe"

@app.get("/", response_class=HTMLResponse)
async def landing_page():
    """Responsive Landing Page for Phone and PC."""
    html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>LocalBot Agency - WhatsApp Automation</title>
        <script src="https://cdn.tailwindcss.com"></script>
    </head>
    <body class="bg-gradient-to-br from-slate-900 via-slate-800 to-indigo-950 min-h-screen text-slate-100 flex flex-col justify-between font-sans">
        <nav class="max-w-6xl w-full mx-auto p-4 md:p-6 flex justify-between items-center">
            <div class="flex items-center gap-2">
                <span class="text-2xl">🤖</span>
                <span class="font-bold text-lg md:text-xl tracking-tight text-white">LocalBot Platform</span>
            </div>
            <div class="flex items-center gap-3">
                <a href="/login" class="bg-emerald-600 hover:bg-emerald-500 text-white font-semibold text-xs md:text-sm px-4 py-2 rounded-lg transition shadow">
                    Shopkeeper Login
                </a>
                <a href="/admin0770" class="text-slate-400 hover:text-white text-xs font-mono transition">
                    Agency Admin
                </a>
            </div>
        </nav>

        <main class="max-w-4xl w-full mx-auto px-4 py-8 text-center my-auto">
            <span class="bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 text-xs uppercase tracking-wider font-semibold px-3 py-1 rounded-full">
                WhatsApp Automation for Local Retailers
            </span>
            <h1 class="text-3xl md:text-5xl font-extrabold text-white mt-4 leading-tight">
                Turn Local Shops into 24/7 WhatsApp Ordering Hubs
            </h1>
            <p class="text-slate-300 text-sm md:text-base mt-4 max-w-2xl mx-auto">
                Automated customer receipts, live owner notifications, and one-click broadcast offers for Kirana, Spices, Salons & Clinics.
            </p>

            <div class="mt-8 flex flex-col sm:flex-row gap-3 justify-center max-w-xs mx-auto">
                <a href="/login" class="bg-emerald-600 hover:bg-emerald-500 text-white font-bold py-3 px-6 rounded-xl shadow-lg transition">
                    Shopkeeper Portal 🛍️
                </a>
                <a href="/admin0770" class="bg-slate-800 hover:bg-slate-700 text-slate-200 font-semibold py-3 px-6 rounded-xl border border-slate-700 transition">
                    Super Admin 🔒
                </a>
            </div>
        </main>

        <footer class="p-6 text-center text-xs text-slate-500 border-t border-slate-800">
            Powered by Meta WhatsApp Cloud API & Fast Vercel Engine
        </footer>
    </body>
    </html>
    """
    return HTMLResponse(content=html)

@app.get("/login", response_class=HTMLResponse)
async def shopkeeper_login(error: Optional[str] = None):
    """Shopkeeper Mobile & Desktop Login."""
    err_banner = f'<div class="bg-rose-50 border border-rose-200 text-rose-700 text-xs p-3 rounded-lg mb-4 text-center font-semibold">{error}</div>' if error else ''
    html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Shopkeeper Portal Login</title>
        <script src="https://cdn.tailwindcss.com"></script>
    </head>
    <body class="bg-slate-100 min-h-screen flex items-center justify-center p-4 font-sans">
        <div class="bg-white rounded-2xl shadow-sm border border-slate-200 p-6 md:p-8 w-full max-w-sm">
            <div class="text-center mb-6">
                <div class="w-12 h-12 bg-emerald-100 text-emerald-700 rounded-full flex items-center justify-center mx-auto mb-2 text-2xl font-bold">
                    🏪
                </div>
                <h1 class="text-xl font-bold text-slate-900">Shopkeeper Login</h1>
                <p class="text-slate-500 text-xs mt-1">Enter your registered shop mobile number and PIN.</p>
            </div>

            {err_banner}

            <form action="/auth/verify" method="post" class="space-y-4">
                <div>
                    <label class="block text-xs font-bold text-slate-700 uppercase mb-1">Registered Phone Number</label>
                    <input type="tel" name="phone" placeholder="e.g. 9818348152 or 9958240721" required class="w-full border border-slate-300 rounded-lg p-2.5 text-sm focus:ring-2 focus:ring-emerald-500">
                </div>

                <div>
                    <label class="block text-xs font-bold text-slate-700 uppercase mb-1">Secret PIN Code</label>
                    <input type="password" name="pin" placeholder="Enter PIN (e.g. 7890)" required class="w-full border border-slate-300 rounded-lg p-2.5 text-sm focus:ring-2 focus:ring-emerald-500 font-mono tracking-widest text-center text-lg">
                </div>

                <button type="submit" class="w-full bg-emerald-600 hover:bg-emerald-500 text-white font-bold py-3 rounded-lg text-sm shadow transition">
                    Open My Store Dashboard 🚀
                </button>
            </form>

            <div class="text-center mt-6">
                <a href="/" class="text-slate-400 hover:text-slate-600 text-xs">← Back to Home</a>
            </div>
        </div>
    </body>
    </html>
    """
    return HTMLResponse(content=html)

@app.post("/auth/verify")
async def verify_auth(phone: str = Form(...), pin: str = Form(...)):
    clean = "".join(ch for ch in phone if ch.isdigit())
    matched_tenant = None

    for tid, profile in tenant_manager.cache.items():
        owner_raw = "".join(ch for ch in profile.get("owner_phone", "") if ch.isdigit())
        if clean.endswith(owner_raw) or owner_raw.endswith(clean):
            tenant_pin = profile.get("pin_code", "7890")
            if pin.strip() == tenant_pin or pin.strip() == "7890":
                matched_tenant = tid
                break

    if matched_tenant:
        return RedirectResponse(url=f"/dashboard?tenant_id={matched_tenant}&auth_key={pin}", status_code=303)

    return RedirectResponse(url="/login?error=Invalid+Phone+Number+or+PIN.+Please+contact+admin.", status_code=303)

# ==================== SUPER ADMIN (Naman: /admin0770) ====================

@app.get("/admin0770", response_class=HTMLResponse)
async def admin_login_page(error: Optional[str] = None):
    """Hidden Super Admin Login Page."""
    err = f'<div class="bg-rose-50 border border-rose-200 text-rose-700 text-xs p-3 rounded-lg mb-4 text-center font-semibold">{error}</div>' if error else ''
    html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Agency Super Admin</title>
        <script src="https://cdn.tailwindcss.com"></script>
    </head>
    <body class="bg-slate-950 min-h-screen flex items-center justify-center p-4 font-sans text-slate-100">
        <div class="bg-slate-900 border border-slate-800 rounded-2xl shadow-xl p-6 md:p-8 w-full max-w-sm">
            <div class="text-center mb-6">
                <div class="w-12 h-12 bg-indigo-500/20 text-indigo-400 rounded-full flex items-center justify-center mx-auto mb-2 text-xl font-mono font-bold">
                    🛡️
                </div>
                <h1 class="text-lg font-bold text-white">Super Admin Access</h1>
                <p class="text-slate-400 text-xs mt-1">Platform Creator & Store Provisioning</p>
            </div>

            {err}

            <form action="/admin0770/login" method="post" class="space-y-4">
                <div>
                    <label class="block text-xs font-mono uppercase text-slate-400 mb-1">Username</label>
                    <input type="text" name="username" placeholder="naman" required class="w-full bg-slate-800 border border-slate-700 rounded-lg p-2.5 text-sm text-white focus:outline-none focus:border-indigo-500">
                </div>

                <div>
                    <label class="block text-xs font-mono uppercase text-slate-400 mb-1">Password</label>
                    <input type="password" name="password" placeholder="••••••••" required class="w-full bg-slate-800 border border-slate-700 rounded-lg p-2.5 text-sm text-white focus:outline-none focus:border-indigo-500">
                </div>

                <button type="submit" class="w-full bg-indigo-600 hover:bg-indigo-500 text-white font-bold py-3 rounded-lg text-sm shadow transition">
                    Authenticate as Naman 🔓
                </button>
            </form>
            <div class="text-center mt-6">
                <a href="/" class="text-slate-500 hover:text-slate-400 text-xs">← Back to Portal</a>
            </div>
        </div>
    </body>
    </html>
    """
    return HTMLResponse(content=html)

@app.post("/admin0770/login")
async def process_admin_login(username: str = Form(...), password: str = Form(...)):
    if username == ADMIN_USER and password == ADMIN_PASS:
        return RedirectResponse(url="/admin0770/dashboard?auth=ok", status_code=303)
    return RedirectResponse(url="/admin0770?error=Invalid+Credentials", status_code=303)

@app.get("/admin0770/dashboard", response_class=HTMLResponse)
async def admin_dashboard(auth: Optional[str] = None):
    """Super Admin Panel: View all shops, add new shops in raw/simple mode."""
    tenants = tenant_manager.cache

    cards_html = ""
    for tid, t in tenants.items():
        cards_html += f"""
        <div class="bg-slate-900 border border-slate-800 rounded-xl p-5 flex flex-col justify-between">
            <div>
                <div class="flex items-center justify-between mb-2">
                    <span class="text-xs bg-indigo-900/50 text-indigo-300 font-mono px-2 py-0.5 rounded border border-indigo-700">{tid}</span>
                    <span class="text-xs text-emerald-400 font-semibold">Active</span>
                </div>
                <h3 class="text-base font-bold text-white">{t.get('business_name')}</h3>
                <p class="text-slate-400 text-xs mt-1">{t.get('category')}</p>
                <div class="text-slate-400 text-xs mt-3 space-y-1">
                    <p>📞 Phone: <span class="text-slate-200">{t.get('phone')}</span></p>
                    <p>🕒 Hours: <span class="text-slate-200">{t.get('hours')}</span></p>
                    <p>🔑 PIN: <span class="text-slate-200 font-mono">{t.get('pin_code', '7890')}</span></p>
                </div>
            </div>
            <div class="mt-4 pt-3 border-t border-slate-800 flex gap-2">
                <a href="/dashboard?tenant_id={tid}&auth_key=7890" target="_blank" class="w-full text-center bg-slate-800 hover:bg-slate-700 text-white text-xs font-semibold py-2 rounded-lg transition">
                    View Shop Portal ↗
                </a>
            </div>
        </div>
        """

    html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Super Admin Dashboard - Naman</title>
        <script src="https://cdn.tailwindcss.com"></script>
    </head>
    <body class="bg-slate-950 text-slate-100 min-h-screen p-4 md:p-8 font-sans">
        <div class="max-w-6xl mx-auto">
            <header class="bg-slate-900 border border-slate-800 rounded-2xl p-5 md:p-6 mb-6 flex flex-col md:flex-row md:items-center md:justify-between">
                <div>
                    <span class="text-xs uppercase font-mono text-indigo-400 tracking-wider">Super Admin Console</span>
                    <h1 class="text-2xl font-bold text-white mt-1">Agency Control Room (Naman)</h1>
                    <p class="text-slate-400 text-xs mt-0.5">Manage existing retail clients and provision new stores on the fly.</p>
                </div>
                <div class="mt-4 md:mt-0 flex gap-3">
                    <a href="/login" class="bg-slate-800 hover:bg-slate-700 text-xs font-semibold px-4 py-2 rounded-lg transition">Shopkeeper Login</a>
                    <a href="/" class="bg-indigo-600 hover:bg-indigo-500 text-xs font-semibold px-4 py-2 rounded-lg transition">Home</a>
                </div>
            </header>

            <div class="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
                <!-- Add New Shop Provisioning Form -->
                <div class="bg-slate-900 border border-slate-800 rounded-2xl p-6">
                    <h2 class="text-lg font-bold text-white mb-2">➕ Add New Shop</h2>
                    <p class="text-slate-400 text-xs mb-4">Enter raw shop details to instantly configure a new client.</p>

                    <form action="/admin0770/add-tenant" method="post" class="space-y-3">
                        <div>
                            <label class="block text-xs font-mono text-slate-400 mb-1">Unique Shop ID (lowercase)</label>
                            <input type="text" name="tenant_id" placeholder="e.g. sharma_sweets" required class="w-full bg-slate-800 border border-slate-700 rounded-lg p-2 text-xs text-white focus:outline-none focus:border-indigo-500">
                        </div>
                        <div>
                            <label class="block text-xs font-mono text-slate-400 mb-1">Shop Name</label>
                            <input type="text" name="business_name" placeholder="e.g. Sharma Sweets & Dairy" required class="w-full bg-slate-800 border border-slate-700 rounded-lg p-2 text-xs text-white focus:outline-none focus:border-indigo-500">
                        </div>
                        <div>
                            <label class="block text-xs font-mono text-slate-400 mb-1">Owner Mobile Number</label>
                            <input type="text" name="phone" placeholder="e.g. 9811002233" required class="w-full bg-slate-800 border border-slate-700 rounded-lg p-2 text-xs text-white focus:outline-none focus:border-indigo-500">
                        </div>
                        <div>
                            <label class="block text-xs font-mono text-slate-400 mb-1">Shop Address</label>
                            <input type="text" name="address" placeholder="e.g. Main Market, Sector 15" required class="w-full bg-slate-800 border border-slate-700 rounded-lg p-2 text-xs text-white focus:outline-none focus:border-indigo-500">
                        </div>
                        <div>
                            <label class="block text-xs font-mono text-slate-400 mb-1">Timings</label>
                            <input type="text" name="hours" placeholder="e.g. 9:00 AM - 9:00 PM" required class="w-full bg-slate-800 border border-slate-700 rounded-lg p-2 text-xs text-white focus:outline-none focus:border-indigo-500">
                        </div>
                        <div>
                            <label class="block text-xs font-mono text-slate-400 mb-1">Secret PIN for Shopkeeper</label>
                            <input type="text" name="pin_code" value="7890" required class="w-full bg-slate-800 border border-slate-700 rounded-lg p-2 text-xs text-white focus:outline-none focus:border-indigo-500 font-mono">
                        </div>
                        <button type="submit" class="w-full bg-emerald-600 hover:bg-emerald-500 text-white font-bold py-2.5 rounded-lg text-xs shadow transition mt-2">
                            Create & Activate Store Bot 🚀
                        </button>
                    </form>
                </div>

                <!-- Stores List -->
                <div class="lg:col-span-2">
                    <div class="flex items-center justify-between mb-4">
                        <h2 class="text-lg font-bold text-white">Active Stores ({len(tenants)})</h2>
                        <span class="text-xs text-slate-400 font-mono">Synced on Vercel</span>
                    </div>
                    <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                        {cards_html}
                    </div>
                </div>
            </div>
        </div>
    </body>
    </html>
    """
    return HTMLResponse(content=html)

@app.post("/admin0770/add-tenant")
async def add_tenant_form(
    tenant_id: str = Form(...),
    business_name: str = Form(...),
    phone: str = Form(...),
    address: str = Form(...),
    hours: str = Form(...),
    pin_code: str = Form("7890"),
):
    clean_id = tenant_id.strip().lower().replace(" ", "_")
    new_data = {
        "tenant_id": clean_id,
        "business_name": business_name.strip(),
        "owner_name": business_name.strip(),
        "category": "Retail & Daily Provisions",
        "address": address.strip(),
        "phone": phone.strip(),
        "owner_phone": phone.strip(),
        "pin_code": pin_code.strip(),
        "hours": hours.strip(),
        "delivery_info": "Standard Doorstep Delivery. Free on orders above ₹499.",
        "payment_methods": "UPI & Cash on Delivery (COD)",
        "featured_items": [
            {"id": "item_1", "name": "Featured Special Product 1", "price": "₹150"},
            {"id": "item_2", "name": "Featured Special Product 2", "price": "₹250"}
        ],
        "faq": [
            {"question": "What are your shop timings?", "answer": f"We are open daily: {hours}."},
            {"question": "Where is the shop located?", "answer": address}
        ]
    }
    tenant_manager.save_tenant(clean_id, new_data)
    return RedirectResponse(url="/admin0770/dashboard?created=ok", status_code=303)

# ==================== WEBHOOK & MESSAGING ====================

@app.get("/webhook")
async def verify_webhook(
    hub_mode: str = Query(None, alias="hub.mode"),
    hub_challenge: str = Query(None, alias="hub.challenge"),
    hub_verify_token: str = Query(None, alias="hub.verify_token"),
):
    if hub_mode == "subscribe" and hub_verify_token == settings.VERIFY_TOKEN:
        logger.info("Webhook verification succeeded.")
        return Response(content=hub_challenge, media_type="text/plain")
    raise HTTPException(status_code=403, detail="Verification token mismatch")

@app.post("/webhook")
async def receive_webhook(request: Request):
    body = await request.json()
    try:
        entry = body.get("entry", [])[0]
        changes = entry.get("changes", [])[0]
        value = changes.get("value", {})
        messages = value.get("messages", [])

        if not messages:
            return {"status": "ignored_non_message"}

        message = messages[0]
        sender_id = message.get("from")

        tenant_id = settings.DEFAULT_TENANT
        profile = tenant_manager.get_tenant(tenant_id)
        if not profile:
            return {"status": "error", "message": "Tenant profile missing"}

        flow = ConversationFlow(tenant_id, profile, whatsapp_service)
        await flow.handle_message(sender_id, message)
        return {"status": "processed"}

    except Exception as e:
        logger.exception(f"Error handling WhatsApp webhook: {e}")
        return {"status": "error", "detail": str(e)}

@app.post("/api/broadcast")
async def trigger_broadcast(
    tenant_id: str = Form(...),
    broadcast_type: str = Form("discount"),
    discount_percent: Optional[int] = Form(None),
    item_focus: Optional[str] = Form(None),
    validity: Optional[str] = Form(None),
    offer_message: Optional[str] = Form(None),
):
    """Broadcast custom discount or raw message to all store customers."""
    if broadcast_type == "discount" and discount_percent:
        res = await broadcast_service.send_broadcast(
            tenant_id=tenant_id,
            discount_percent=discount_percent,
            item_focus=item_focus or "all products",
            validity=validity or "today only",
        )
    else:
        res = await broadcast_service.send_broadcast(
            tenant_id=tenant_id,
            offer_message=offer_message,
        )

    sent = res.get("sent_count", 0)
    return RedirectResponse(url=f"/dashboard?tenant_id={tenant_id}&broadcast_sent={sent}", status_code=303)

@app.get("/dashboard", response_class=HTMLResponse)
async def shop_owner_dashboard(tenant_id: str = "praveen_general_store", broadcast_sent: int = None):
    """Shop Owner Mobile & Desktop Portal."""
    profile = tenant_manager.get_tenant(tenant_id) or {}
    shop_name = profile.get("business_name", "Shop Portal")
    category = profile.get("category", "")
    owner_phone = profile.get("owner_phone", "+919818348152")

    orders = db.list_orders(tenant_id)
    subscribers = db.get_broadcast_subscribers(tenant_id)
    broadcast_history = db.list_broadcasts(tenant_id)

    order_rows = ""
    for o in orders:
        raw_items = ""
        for it in o.get("items", []):
            if isinstance(it, dict) and "raw_list" in it:
                raw_items += it["raw_list"]
            else:
                raw_items += str(it)

        order_rows += f"""
        <tr class="border-b hover:bg-slate-50">
            <td class="p-3 font-bold text-slate-800">#{o['id']}</td>
            <td class="p-3 font-medium text-slate-700">{o['customer_phone']}</td>
            <td class="p-3 text-slate-900 whitespace-pre-line font-mono text-xs bg-slate-50 rounded p-2">{raw_items}</td>
            <td class="p-3 text-slate-600 text-xs">{o['delivery_address'] or 'Pick Up in Store'}</td>
            <td class="p-3"><span class="bg-amber-100 text-amber-800 px-2 py-0.5 rounded text-xs font-semibold uppercase">{o['status']}</span></td>
            <td class="p-3 text-slate-400 text-xs">{o['created_at']}</td>
        </tr>
        """
    if not order_rows:
        order_rows = "<tr><td colspan='6' class='p-8 text-center text-slate-400'>No orders received yet.</td></tr>"

    banner_html = ""
    if broadcast_sent is not None:
        banner_html = f"""
        <div class="mb-6 p-4 bg-emerald-50 border border-emerald-200 text-emerald-800 rounded-xl flex items-center gap-2 shadow-sm">
            <span class="text-xl">✅</span>
            <div><strong>Broadcast Dispatched!</strong> Sent offer to <strong>{broadcast_sent} customers</strong> on WhatsApp!</div>
        </div>
        """

    broadcast_rows = ""
    for b in broadcast_history:
        broadcast_rows += f"""
        <tr class="border-b text-xs">
            <td class="p-3 text-slate-500 whitespace-nowrap">{b['sent_at']}</td>
            <td class="p-3 font-medium text-slate-800 whitespace-pre-line">{b['message_text']}</td>
            <td class="p-3 text-emerald-600 font-bold whitespace-nowrap">{b['recipients_count']} sent</td>
        </tr>
        """

    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{shop_name} - Owner Portal</title>
        <script src="https://cdn.tailwindcss.com"></script>
    </head>
    <body class="bg-slate-100 min-h-screen p-3 md:p-8 font-sans">
        <div class="max-w-6xl mx-auto">
            {banner_html}
            <header class="bg-white rounded-xl shadow-sm p-5 md:p-6 mb-6 flex flex-col md:flex-row md:items-center md:justify-between border border-slate-200">
                <div>
                    <div class="flex items-center gap-2">
                        <span class="text-xs uppercase tracking-wider font-semibold text-emerald-600 bg-emerald-50 px-2.5 py-1 rounded-md border border-emerald-200">{category}</span>
                        <span class="text-xs text-slate-400">Owner: {owner_phone}</span>
                    </div>
                    <h1 class="text-2xl font-bold text-slate-900 mt-2">{shop_name}</h1>
                    <p class="text-slate-500 text-sm mt-0.5">{profile.get('address')} | Hours: {profile.get('hours')}</p>
                </div>
                <div class="mt-4 md:mt-0 flex gap-2">
                    <span class="inline-flex items-center gap-1.5 bg-emerald-50 text-emerald-700 border border-emerald-200 px-3 py-1.5 rounded-lg text-xs font-semibold">
                        <span class="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span> WhatsApp Live
                    </span>
                    <a href="/login" class="bg-slate-200 hover:bg-slate-300 text-slate-700 text-xs font-semibold px-3 py-2 rounded-lg transition">Switch Shop</a>
                    <a href="/dashboard?tenant_id={tenant_id}" class="bg-slate-900 text-white hover:bg-slate-800 text-xs font-medium px-4 py-2 rounded-lg transition">Refresh</a>
                </div>
            </header>

            <div class="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
                <!-- Custom % Discount Blaster to All Store Customers -->
                <div class="bg-white rounded-xl shadow-sm border border-slate-200 p-5 md:p-6">
                    <div class="flex items-center justify-between mb-2">
                        <h2 class="font-bold text-slate-800 text-lg">📢 Blast Customer Offer</h2>
                        <span class="text-xs bg-indigo-50 text-indigo-700 font-bold px-2 py-0.5 rounded-full">{len(subscribers)} Customers</span>
                    </div>
                    <p class="text-xs text-slate-500 mb-4">Set up a discount % and blast it directly to all customers who ever bought from you.</p>

                    <form action="/api/broadcast" method="post" class="space-y-4">
                        <input type="hidden" name="tenant_id" value="{tenant_id}">
                        <input type="hidden" name="broadcast_type" value="discount">

                        <div>
                            <label class="block text-xs font-bold text-slate-700 uppercase mb-1">Discount %</label>
                            <div class="flex items-center gap-2">
                                <input type="number" name="discount_percent" min="1" max="90" value="10" class="w-full border border-slate-300 rounded-lg p-2.5 text-sm font-bold text-emerald-600 focus:ring-2 focus:ring-emerald-500" required>
                                <span class="text-sm font-bold text-slate-500">% OFF</span>
                            </div>
                        </div>

                        <div>
                            <label class="block text-xs font-bold text-slate-700 uppercase mb-1">Valid On</label>
                            <input type="text" name="item_focus" value="All Items & Daily Groceries" class="w-full border border-slate-300 rounded-lg p-2.5 text-sm focus:ring-2 focus:ring-emerald-500">
                        </div>

                        <div>
                            <label class="block text-xs font-bold text-slate-700 uppercase mb-1">Offer Time</label>
                            <input type="text" name="validity" value="Today 10 AM to 10 PM Only" class="w-full border border-slate-300 rounded-lg p-2.5 text-sm focus:ring-2 focus:ring-emerald-500">
                        </div>

                        <button type="submit" class="w-full bg-emerald-600 hover:bg-emerald-500 text-white font-bold py-3 rounded-lg text-sm shadow transition">
                            Blast WhatsApp Offer to All Customers 🚀
                        </button>
                    </form>
                </div>

                <!-- Live Orders Section -->
                <div class="lg:col-span-2 bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
                    <div class="p-5 border-b border-slate-200 flex justify-between items-center bg-slate-50">
                        <div>
                            <h2 class="font-bold text-slate-800">🛒 Recent Customer Orders ({len(orders)})</h2>
                            <p class="text-xs text-slate-500">Auto-synced from WhatsApp chats</p>
                        </div>
                    </div>
                    <div class="overflow-x-auto max-h-[460px]">
                        <table class="w-full text-left text-sm border-collapse">
                            <thead>
                                <tr class="bg-slate-100 text-slate-600 text-xs uppercase tracking-wider font-semibold border-b">
                                    <th class="p-3">ID</th>
                                    <th class="p-3">Customer</th>
                                    <th class="p-3">Order Details</th>
                                    <th class="p-3">Address</th>
                                    <th class="p-3">Status</th>
                                    <th class="p-3">Time</th>
                                </tr>
                            </thead>
                            <tbody>
                                {order_rows}
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>

            <!-- Campaign History -->
            <div class="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
                <div class="p-4 border-b border-slate-200 bg-slate-50 flex justify-between items-center">
                    <h3 class="font-bold text-slate-800 text-sm">Dispatched Discount Campaigns ({len(broadcast_history)})</h3>
                </div>
                <div class="overflow-x-auto">
                    <table class="w-full text-left text-sm">
                        <thead>
                            <tr class="bg-slate-100 text-slate-500 text-xs uppercase border-b">
                                <th class="p-3">Date</th>
                                <th class="p-3">Message Sent to WhatsApp</th>
                                <th class="p-3">Delivered</th>
                            </tr>
                        </thead>
                        <tbody>
                            {broadcast_rows or "<tr><td colspan='3' class='p-4 text-center text-slate-400 text-xs'>No campaigns sent yet.</td></tr>"}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)
