"""
Single-command launcher for Smart Civic Complaint & Issue Management System.
Starts the FastAPI server with auto-reload and serves the web frontend.
"""

import sys
import os
import uvicorn

# Ensure the backend directory is in the Python search path
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.join(ROOT_DIR, "backend")
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

if __name__ == "__main__":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    port = int(os.environ.get("PORT", 8000))
    host = os.environ.get("HOST", "0.0.0.0")
    is_prod = bool(os.environ.get("PORT") or os.environ.get("RAILWAY_ENVIRONMENT"))

    print("\n" + "=" * 70)
    print(" [*] CIVIC COMPLAINT & OPERATIONS PORTAL")
    print("=" * 70)
    print(f" Web Application Portal : http://{host}:{port}/")
    print(f" Interactive API Docs   : http://{host}:{port}/docs")
    print(f" Executive Analytics    : http://{host}:{port}/#view-analytics")
    print(f" Bonus AI NLP Engine    : Enabled (Automatic classification & Work Orders)")
    print("=" * 70 + "\n")

    uvicorn.run("app.main:app", host=host, port=port, reload=not is_prod)

