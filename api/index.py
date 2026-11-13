import os
import sys

# Ensure root directory is properly recognized by Vercel
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

try:
    from src.app import app
except Exception as e:
    import traceback
    from fastapi import FastAPI
    from fastapi.responses import PlainTextResponse

    app = FastAPI()

    @app.get("/{full_path:path}")
    def catch_all(full_path: str):
        error_msg = traceback.format_exc()
        return PlainTextResponse(f"Startup Exception:\n{error_msg}", status_code=500)
