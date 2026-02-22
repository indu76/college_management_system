"""
Outpass Management System - FastAPI Application
"""

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path

from tutor_routes import router as tutor_router
from warden_routes import router as warden_router

app = FastAPI(title="Outpass Management System", version="1.0.0")

# Include routers
app.include_router(tutor_router)
app.include_router(warden_router)

# Paths
BASE_DIR = Path(__file__).resolve().parent
TEMPLATES_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"

# Mount static files
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


# --- Serve HTML pages ---
@app.get("/")
def root():
    return FileResponse(TEMPLATES_DIR / "tutor_login.html")


@app.get("/tutor_login.html")
def tutor_login_page():
    return FileResponse(TEMPLATES_DIR / "tutor_login.html")


@app.get("/tutor_dashboard.html")
def tutor_dashboard_page():
    return FileResponse(TEMPLATES_DIR / "tutor_dashboard.html")


@app.get("/warden_login.html")
def warden_login_page():
    return FileResponse(TEMPLATES_DIR / "warden_login.html")


@app.get("/warden_dashboard.html")
def warden_dashboard_page():
    return FileResponse(TEMPLATES_DIR / "warden_dashboard.html")
