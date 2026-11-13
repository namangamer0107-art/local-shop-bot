import os
import sys
from fastapi import FastAPI, Request, Query, Response, HTTPException, Form
from fastapi.responses import HTMLResponse, RedirectResponse

# Ensure root directory is in sys.path
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

# Top-level FastAPI instance required by Vercel Python runtime
app = FastAPI(
    title="Local Shop WhatsApp Bot Platform",
    description="Multi-tenant WhatsApp AI booking, ordering, discount campaigns, and customer support for local businesses.",
    version="2.0.0",
)

# Export handler alias for Vercel WSGI/ASGI detector
handler = app

# Import all route definitions from src.app onto this top-level app
try:
    from src.app import app as main_app
    app.router = main_app.router
except Exception as e:
    import traceback
    err_trace = traceback.format_exc()
    @app.get("/{full_path:path}")
    def fallback(full_path: str):
        return HTMLResponse(f"<pre style='color:red;'>Initialization Error:\n{err_trace}</pre>", status_code=500)
