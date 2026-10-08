import os
import json
from pathlib import Path
from typing import Dict, Any, Optional
from fastapi import FastAPI, Request, HTTPException, UploadFile, File
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

WEB_DIR = BASE_DIR / "web"
STATIC_DIR = WEB_DIR / "static"
TEMPLATES_DIR = WEB_DIR / "templates"
VIDEOS_DIR = BASE_DIR / "data" / "videos"
SHOWROOM_DIR = BASE_DIR / "showroom"
VIDEOS_DIR.mkdir(parents=True, exist_ok=True)
SHOWROOM_DIR.mkdir(parents=True, exist_ok=True)

app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
app.mount("/images", StaticFiles(directory=str(IMAGE_DIR)), name="images")
app.mount("/videos", StaticFiles(directory=str(VIDEOS_DIR)), name="videos")

templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

# Global scheduler instance
scheduler_instance = AutoPilotScheduler()


class TriggerRequest(BaseModel):
    force_affiliate: bool = True


class SettingsUpdateRequest(BaseModel):
    config: Dict[str, Any]


class ProductLinkUpdateRequest(BaseModel):
    product_id: str
    new_link: str


@app.on_event("startup")
def startup_event():
    cfg = load_config()
    from modules.showroom.builder import ShowroomBuilder
    ShowroomBuilder.build_showroom_html()
    if cfg.get("strategy", {}).get("auto_pilot_enabled", True):
        scheduler_instance.start()
        save_log("INFO", "system", "Auto-Pilot automation started on startup.")


@app.get("/", response_class=HTMLResponse)
async def serve_index(request: Request):
    return templates.TemplateResponse(request=request, name="index.html")


@app.get("/showroom", response_class=HTMLResponse)
async def serve_showroom():
    from modules.showroom.builder import ShowroomBuilder, SHOWROOM_HTML_PATH
    if not SHOWROOM_HTML_PATH.exists():
        ShowroomBuilder.build_showroom_html()
    with open(SHOWROOM_HTML_PATH, "r", encoding="utf-8") as f:
        return f.read()


@app.post("/api/trigger/shorts")
def trigger_shorts():
    try:
        res = scheduler_instance.trigger_shorts_cycle()
        return {"success": True, "data": res}
    except Exception as e:
        save_log("ERROR", "api", f"Shorts trigger error: {e}")
        return {"success": False, "error": str(e)}


@app.post("/api/trigger/threads")
def trigger_threads():
    try:
        res = scheduler_instance.trigger_one_post(force_affiliate=True)
        return {"success": True, "data": res}
    except Exception as e:
        save_log("ERROR", "api", f"Threads trigger error: {e}")
        return {"success": False, "error": str(e)}


@app.get("/api/videos")
async def get_videos():
    from datetime import datetime
    videos = []
    for f in sorted(VIDEOS_DIR.glob("*.mp4"), key=os.path.getmtime, reverse=True):
        videos.append({
            "filename": f.name,
            "size_mb": round(f.stat().st_size / (1024 * 1024), 2),
            "created_at": datetime.fromtimestamp(f.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
            "url": f"/videos/{f.name}"
        })
    return videos


@app.get("/api/youtube/status")
def get_youtube_status():
    from modules.publisher.youtube_api import YouTubePublisher
    yt = YouTubePublisher()
    profile = yt.get_channel_profile() if yt.is_authenticated() else None
    return {
        "enabled": yt.enabled,
        "is_authenticated": yt.is_authenticated(),
        "has_credentials": yt.has_credentials(),
        "secrets_file_exists": yt.secrets_file.exists(),
        "privacy_status": yt.privacy_status,
        "channel_profile": profile,
        "local_videos_count": len(list(VIDEOS_DIR.glob("*.mp4")))
    }


@app.post("/api/youtube/upload-secrets")
async def upload_youtube_secrets(file: UploadFile = File(...)):
    try:
        content = await file.read()
        data = json.loads(content.decode("utf-8"))
        if "installed" not in data and "web" not in data:
            return JSONResponse(status_code=400, content={"success": False, "error": "올바른 Google OAuth 클라이언트 JSON(client_secrets.json) 형식이 아닙니다."})

        target_path = BASE_DIR / "config" / "client_secrets.json"
        with open(target_path, "wb") as f:
            f.write(content)
        save_log("INFO", "youtube", "client_secrets.json uploaded successfully via web dashboard.")
        return {"success": True, "message": "Google OAuth client_secrets.json 파일이 성공적으로 등록되었습니다!"}
    except Exception as e:
        save_log("ERROR", "youtube", f"Failed to upload client_secrets.json: {e}")
        return JSONResponse(status_code=500, content={"success": False, "error": str(e)})


@app.post("/api/youtube/authenticate")
def authenticate_youtube():
    from modules.publisher.youtube_api import YouTubePublisher
    yt = YouTubePublisher()
    res = yt.authenticate_interactive()
    return res


@app.post("/api/youtube/disconnect")
def disconnect_youtube():
    from modules.publisher.youtube_api import YouTubePublisher
    yt = YouTubePublisher()
    success = yt.disconnect()
    return {"success": success}


@app.post("/api/youtube/reset-auth")
def reset_youtube_auth():
    save_log("INFO", "youtube", "YouTube auth state reset requested.")
    return {"success": True, "message": "인증 상태가 초기화되었습니다."}




@app.post("/api/showroom/deploy-github")
def deploy_showroom_to_github():
    import subprocess
    from modules.showroom.builder import ShowroomBuilder
    ShowroomBuilder.build_showroom_html()
    try:
        check_remote = subprocess.run(["git", "remote"], cwd=str(BASE_DIR), capture_output=True, text=True)
        if not check_remote.stdout.strip():
            return {
                "success": False,
                "error": "GitHub 원격 저장소가 등록되어 있지 않습니다. 터미널에서 'git remote add origin https://github.com/아이디/저장소.git'를 먼저 등록해주세요."
            }
        subprocess.run(["git", "add", "docs/", "showroom/"], cwd=str(BASE_DIR), check=True)
        subprocess.run(["git", "commit", "-m", "Auto-update showroom catalog for GitHub Pages"], cwd=str(BASE_DIR))
        res = subprocess.run(["git", "push"], cwd=str(BASE_DIR), capture_output=True, text=True)
        if res.returncode == 0:
            save_log("INFO", "showroom", "Showroom successfully deployed to GitHub Pages via git push!")
            return {"success": True, "message": "GitHub Pages로 모바일 쇼룸 배포가 완료되었습니다!"}
        else:
            return {"success": False, "error": f"Git push 실패: {res.stderr}"}
    except Exception as e:
        return {"success": False, "error": str(e)}


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
def trigger_manual_post(req: TriggerRequest):
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
    return get_recent_products(limit=100)


@app.post("/api/products/update-link")
async def update_link(req: ProductLinkUpdateRequest):
    from database.db import update_product_link
    from modules.showroom.builder import ShowroomBuilder
    success = update_product_link(req.product_id, req.new_link)
    if success:
        ShowroomBuilder.build_showroom_html()
        return {"success": True, "message": "상품 링크가 성공적으로 수정되었고 쇼룸에 즉시 반영되었습니다!"}
    raise HTTPException(status_code=400, detail="링크 업데이트 실패")


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
