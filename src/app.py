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
    title="Local Shop WhatsApp Bot Platform",
    description="Multi-tenant WhatsApp AI booking, ordering, discount campaigns, and customer support for local businesses.",
    version="2.0.0",
)

whatsapp_service = WhatsAppService()
broadcast_service = BroadcastService(whatsapp_service)

# Default Master PIN for you/agency: 7890
MASTER_PIN = "7890"

@app.get("/")
async def root():
    return {
        "status": "online",
        "service": "Local Shop WhatsApp Bot Platform",
        "tenants_loaded": list(tenant_manager.cache.keys()),
        "dashboard_login": "/login",
    }

@app.get("/webhook")
async def verify_webhook(
    hub_mode: str = Query(None, alias="hub.mode"),
    hub_challenge: str = Query(None, alias="hub.challenge"),
    hub_verify_token: str = Query(None, alias="hub.verify_token"),
):
    """Webhook verification endpoint for Meta WhatsApp Cloud API."""
    if hub_mode == "subscribe" and hub_verify_token == settings.VERIFY_TOKEN:
        logger.info("Webhook verification succeeded.")
        return Response(content=hub_challenge, media_type="text/plain")
    logger.warning("Webhook verification failed. Token mismatch.")
    raise HTTPException(status_code=403, detail="Verification token mismatch")

@app.post("/webhook")
async def receive_webhook(request: Request):
    """Receives incoming WhatsApp events (messages, button clicks, status updates)."""
    body = await request.json()
    logger.info(f"Incoming WhatsApp payload: {body}")

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
            logger.error(f"Tenant profile not found for {tenant_id}")
            return {"status": "error", "message": "Tenant profile missing"}

        flow = ConversationFlow(tenant_id, profile, whatsapp_service)
        await flow.handle_message(sender_id, message)

        return {"status": "processed"}

    except Exception as e:
        logger.exception(f"Error handling WhatsApp webhook: {e}")
        return {"status": "error", "detail": str(e)}

@app.get("/login", response_class=HTMLResponse)
async def login_page(error: Optional[str] = None):
    """Secure Mobile Login Page for Shopkeepers using their Phone & Secret PIN."""
    error_html = f'<p class="text-rose-600 text-xs mb-4 text-center font-semibold bg-rose-50 p-2.5 rounded-lg border border-rose-200">{error}</p>' if error else ''
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Shop Owner Portal - Login</title>
        <script src="https://cdn.tailwindcss.com"></script>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
    </head>
    <body class="bg-slate-100 flex items-center justify-center min-h-screen p-4 font-sans">
        <div class="bg-white rounded-2xl shadow-md border border-slate-200 p-6 md:p-8 w-full max-w-sm">
            <div class="text-center mb-6">
                <div class="w-12 h-12 bg-emerald-100 text-emerald-700 rounded-full flex items-center justify-center mx-auto mb-3 font-bold text-xl">
                    🛍️
                </div>
                <h1 class="text-xl font-bold text-slate-800">Shopkeeper Login</h1>
                <p class="text-slate-500 text-xs mt-1">Enter your registered mobile number and unique security PIN.</p>
            </div>

            {error_html}

            <form action="/auth/verify" method="post" class="space-y-4">
                <div>
                    <label class="block text-xs font-bold text-slate-700 uppercase mb-1">Registered Phone Number</label>
                    <input type="tel" name="phone" placeholder="e.g. 9818348152" required class="w-full border border-slate-300 rounded-lg p-2.5 text-sm focus:ring-2 focus:ring-emerald-500">
                </div>

                <div>
                    <label class="block text-xs font-bold text-slate-700 uppercase mb-1">Secret PIN Code</label>
                    <input type="password" name="pin" placeholder="Enter 4-digit PIN" required class="w-full border border-slate-300 rounded-lg p-2.5 text-sm focus:ring-2 focus:ring-emerald-500 font-mono tracking-widest text-center text-lg">
                </div>

                <button type="submit" class="w-full bg-slate-900 hover:bg-slate-800 text-white font-bold py-3 rounded-lg text-sm shadow transition">
                    Open My Shop Portal 🔓
                </button>
            </form>
            <p class="text-slate-400 text-xs text-center mt-6">Protected with Secret Tenant Authentication</p>
        </div>
    </body>
    </html>
    """
    return HTMLResponse(content=html)

@app.post("/auth/verify")
async def verify_auth(phone: str = Form(...), pin: str = Form(...)):
    """Verifies phone and PIN code, then routes shopkeeper to their specific store dashboard."""
    clean_phone = "".join(ch for ch in phone if ch.isdigit())

    # Search loaded tenants for matching owner phone
    matched_tenant = None
    for tid, profile in tenant_manager.cache.items():
        owner_raw = "".join(ch for ch in profile.get("owner_phone", "") if ch.isdigit())
        if clean_phone.endswith(owner_raw) or owner_raw.endswith(clean_phone):
            tenant_pin = profile.get("pin_code", MASTER_PIN)
            if pin.strip() == tenant_pin or pin.strip() == MASTER_PIN:
                matched_tenant = tid
                break

    if matched_tenant:
        return RedirectResponse(url=f"/dashboard?tenant_id={matched_tenant}&auth_key={pin}", status_code=303)
    
    return RedirectResponse(url="/login?error=Invalid+Phone+Number+or+PIN+Code.+Please+check+with+your+provider.", status_code=303)

@app.post("/api/broadcast")
async def trigger_broadcast(
    tenant_id: str = Form(...),
    broadcast_type: str = Form("discount"),
    discount_percent: Optional[int] = Form(None),
    item_focus: Optional[str] = Form(None),
    validity: Optional[str] = Form(None),
    offer_message: Optional[str] = Form(None),
):
    """API endpoint for sending automatic discount campaigns."""
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
    return RedirectResponse(
        url=f"/dashboard?tenant_id={tenant_id}&broadcast_sent={sent}",
        status_code=303
    )

@app.get("/dashboard", response_class=HTMLResponse)
async def shop_owner_dashboard(tenant_id: str = "praveen_general_store", broadcast_sent: int = None):
    """Visual Dashboard for Shop Owners."""
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
        <tr class="border-b hover:bg-amber-50/50">
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
            <div>
                <strong>Broadcast Dispatched!</strong> Successfully sent your promotional offer to <strong>{broadcast_sent} customers</strong> on WhatsApp!
            </div>
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
    <html>
    <head>
        <title>{shop_name} - Owner Portal & Offers</title>
        <script src="https://cdn.tailwindcss.com"></script>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
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
                    <p class="text-slate-500 text-sm mt-0.5">{profile.get('address')} | Timings: {profile.get('hours')}</p>
                </div>
                <div class="mt-4 md:mt-0 flex gap-3">
                    <span class="inline-flex items-center gap-1.5 bg-emerald-50 text-emerald-700 border border-emerald-200 px-3 py-1.5 rounded-lg text-xs font-semibold">
                        <span class="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span> WhatsApp Live
                    </span>
                    <a href="/login" class="bg-slate-200 hover:bg-slate-300 text-slate-700 text-xs font-semibold px-3 py-2 rounded-lg transition">Switch Shop</a>
                    <a href="/dashboard?tenant_id={tenant_id}" class="bg-slate-900 text-white hover:bg-slate-800 text-xs font-medium px-4 py-2 rounded-lg transition">Refresh</a>
                </div>
            </header>

            <div class="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
                <!-- Custom % Discount & Daily Offer Creator -->
                <div class="bg-white rounded-xl shadow-sm border border-slate-200 p-5 md:p-6">
                    <div class="flex items-center justify-between mb-2">
                        <h2 class="font-bold text-slate-800 text-lg">🎯 Launch Customer Offer</h2>
                        <span class="text-xs bg-indigo-50 text-indigo-700 font-bold px-2 py-0.5 rounded-full">{len(subscribers)} Customer Contacts</span>
                    </div>
                    <p class="text-xs text-slate-500 mb-4">Set up any discount % or announcement and blast it instantly to all customers on WhatsApp.</p>
                    
                    <form action="/api/broadcast" method="post" class="space-y-4">
                        <input type="hidden" name="tenant_id" value="{tenant_id}">
                        <input type="hidden" name="broadcast_type" value="discount">
                        
                        <div>
                            <label class="block text-xs font-bold text-slate-700 uppercase mb-1">Discount Percentage (%)</label>
                            <div class="flex items-center gap-2">
                                <input type="number" name="discount_percent" min="1" max="90" value="10" class="w-full border border-slate-300 rounded-lg p-2.5 text-sm font-bold text-emerald-600 focus:ring-2 focus:ring-emerald-500" required>
                                <span class="text-sm font-bold text-slate-500">% OFF</span>
                            </div>
                        </div>

                        <div>
                            <label class="block text-xs font-bold text-slate-700 uppercase mb-1">Applicable On</label>
                            <input type="text" name="item_focus" value="All Namkeen, Biscuits & Fresh Atta" class="w-full border border-slate-300 rounded-lg p-2.5 text-sm focus:ring-2 focus:ring-emerald-500">
                        </div>

                        <div>
                            <label class="block text-xs font-bold text-slate-700 uppercase mb-1">Offer Validity</label>
                            <input type="text" name="validity" value="Today 10 AM to 10 PM Only" class="w-full border border-slate-300 rounded-lg p-2.5 text-sm focus:ring-2 focus:ring-emerald-500">
                        </div>

                        <button type="submit" class="w-full bg-emerald-600 hover:bg-emerald-700 text-white font-bold py-3 rounded-lg text-sm shadow transition">
                            Blast WhatsApp Offer to All Customers 🚀
                        </button>
                    </form>
                </div>

                <!-- Live Orders Section -->
                <div class="lg:col-span-2 bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
                    <div class="p-5 border-b border-slate-200 flex justify-between items-center bg-slate-50">
                        <div>
                            <h2 class="font-bold text-slate-800">🛒 Recent Customer Orders ({len(orders)})</h2>
                            <p class="text-xs text-slate-500">Auto-synced from customer WhatsApp messages</p>
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
