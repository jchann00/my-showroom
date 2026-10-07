import os
import json
from pathlib import Path
from typing import Dict, Any, Optional
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from config.settings import load_config, save_config, BASE_DIR, IMAGE_DIR
from database.db import (
    get_stats, get_recent_posts, get_recent_products, get_recent_logs, save_log
)
from modules.scheduler.auto_pilot import AutoPilotScheduler

app = FastAPI(title="Threads & Instagram Monetization Automation")

# Mount static and image directories
STATIC_DIR = BASE_DIR / "web" / "static"
TEMPLATES_DIR = BASE_DIR / "web" / "templates"

app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
app.mount("/images", StaticFiles(directory=str(IMAGE_DIR)), name="images")

templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

# Global scheduler instance
scheduler_instance = AutoPilotScheduler()


class TriggerRequest(BaseModel):
    force_affiliate: bool = True


class SettingsUpdateRequest(BaseModel):
    config: Dict[str, Any]


@app.on_event("startup")
def startup_event():
    cfg = load_config()
    if cfg.get("strategy", {}).get("auto_pilot_enabled", True):
        scheduler_instance.start()
        save_log("INFO", "system", "Auto-Pilot automation started on startup.")


@app.get("/", response_class=HTMLResponse)
async def serve_index(request: Request):
    return templates.TemplateResponse(request=request, name="index.html")


@app.get("/api/status")
async def get_system_status():
    cfg = load_config()
    stats = get_stats()
    return {
        "is_running": scheduler_instance.is_running,
        "stats": stats,
        "config": cfg,
        "golden_hours": cfg.get("strategy", {}).get("golden_hours", []),
    }


@app.post("/api/trigger")
async def trigger_manual_post(req: TriggerRequest):
    try:
        res = scheduler_instance.trigger_one_post(force_affiliate=req.force_affiliate)
        return {"success": True, "data": res}
    except Exception as e:
        save_log("ERROR", "api", f"Manual trigger failed: {e}")
        return {"success": False, "error": str(e)}


@app.post("/api/scheduler/toggle")
async def toggle_scheduler():
    if scheduler_instance.is_running:
        scheduler_instance.stop()
        state = False
    else:
        scheduler_instance.start()
        state = True
    return {"is_running": state}


@app.get("/api/products")
async def get_products():
    return get_recent_products(limit=50)


@app.get("/api/posts")
async def get_posts():
    return get_recent_posts(limit=30)


@app.get("/api/logs")
async def get_logs():
    return get_recent_logs(limit=60)


@app.post("/api/settings")
async def update_settings(req: SettingsUpdateRequest):
    try:
        save_config(req.config)
        # Reload scheduler with new golden hours
        if scheduler_instance.is_running:
            scheduler_instance.stop()
            scheduler_instance.start()
        save_log("INFO", "config", "Settings updated successfully via Web Dashboard.")
        return {"success": True}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
