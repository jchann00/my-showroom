import os
import json
import time
from pathlib import Path
from typing import Dict, Any, Optional, List
from config.settings import BASE_DIR, load_config
from database.db import save_log

# Google API client imports
try:
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload
    from googleapiclient.errors import HttpError
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    from google_auth_oauthlib.flow import InstalledAppFlow
    GOOGLE_LIBS_AVAILABLE = True
except ImportError:
    GOOGLE_LIBS_AVAILABLE = False

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]


class YouTubePublisher:
    """Automated YouTube Shorts Uploader with OAuth 2.0 and Unattended Refresh Token."""

    def __init__(self):
        self.cfg = load_config()
        yt_cfg = self.cfg.get("youtube", {})
        self.enabled = yt_cfg.get("enabled", True)
        self.privacy_status = yt_cfg.get("privacy_status", "public")
        self.simulation_mode = yt_cfg.get("simulation_mode", False)
        
        self.secrets_file = BASE_DIR / "config" / "client_secrets.json"
        self.token_file = BASE_DIR / "config" / "youtube_token.json"

    def has_credentials(self) -> bool:
        """Checks if client secrets or saved token exists."""
        return self.token_file.exists() or self.secrets_file.exists()

    def is_authenticated(self) -> bool:
        """Checks if valid, authorized credentials already exist."""
        if not self.token_file.exists():
            return False
        try:
            creds = Credentials.from_authorized_user_file(str(self.token_file), SCOPES)
            return bool(creds and (creds.valid or creds.refresh_token))
        except Exception:
            return False

    def get_service(self):
        """Authenticates with YouTube Data API v3 and returns the service resource."""
        if not GOOGLE_LIBS_AVAILABLE:
            raise RuntimeError("google-api-python-client 라이브러리가 설치되지 않았습니다.")

        creds = None
        # 1. Load existing token
        if self.token_file.exists():
            try:
                creds = Credentials.from_authorized_user_file(str(self.token_file), SCOPES)
            except Exception as e:
                save_log("WARNING", "youtube", f"Failed to load youtube_token.json: {e}")
                creds = None

        # 2. Refresh or trigger browser login
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    save_log("INFO", "youtube", "Refreshing expired YouTube OAuth access token...")
                    creds.refresh(Request())
                    with open(self.token_file, "w", encoding="utf-8") as f:
                        f.write(creds.to_json())
                except Exception as e:
                    save_log("ERROR", "youtube", f"Failed to refresh YouTube token: {e}")
                    creds = None

            if not creds:
                if not self.secrets_file.exists():
                    raise FileNotFoundError(
                        f"Google Cloud 콘솔에서 다운로드한 'client_secrets.json' 파일이 필요합니다.\n"
                        f"저장 위치: {self.secrets_file}"
                    )
                save_log("INFO", "youtube", "Starting 1-time browser authentication for YouTube...")
                flow = InstalledAppFlow.from_client_secrets_file(str(self.secrets_file), SCOPES)
                creds = flow.run_local_server(port=0, prompt="consent", access_type="offline")
                with open(self.token_file, "w", encoding="utf-8") as f:
                    f.write(creds.to_json())
                save_log("INFO", "youtube", "YouTube authorization successful! Token saved for 24/7 automation.")

        return build("youtube", "v3", credentials=creds)

    def get_channel_profile(self) -> Optional[Dict[str, Any]]:
        """Returns channel title, customUrl, thumbnail, subscribers if authorized."""
        if not self.is_authenticated():
            return None
        try:
            yt = self.get_service()
            res = yt.channels().list(part="snippet,statistics", mine=True).execute()
            items = res.get("items", [])
            if items:
                ch = items[0]
                return {
                    "id": ch.get("id"),
                    "title": ch.get("snippet", {}).get("title"),
                    "custom_url": ch.get("snippet", {}).get("customUrl", ""),
                    "subscribers": ch.get("statistics", {}).get("subscriberCount", "0"),
                    "thumbnail": ch.get("snippet", {}).get("thumbnails", {}).get("default", {}).get("url", "")
                }
        except Exception as e:
            save_log("WARNING", "youtube", f"Failed to get channel profile: {e}")
            return None
        return None

    def authenticate_interactive(self, timeout: int = 90) -> Dict[str, Any]:
        """Triggers local browser login flow for YouTube channel authorization."""
        if not self.secrets_file.exists():
            return {
                "success": False,
                "error": "client_secrets.json 파일이 없습니다. Google Cloud 콘솔에서 발급받은 OAuth 클라이언트 JSON 파일을 먼저 업로드해주세요."
            }
        try:
            flow = InstalledAppFlow.from_client_secrets_file(str(self.secrets_file), SCOPES)
            save_log("INFO", "youtube", f"Starting browser OAuth login (timeout {timeout}s)...")
            creds = flow.run_local_server(
                port=0,
                prompt="consent",
                access_type="offline",
                timeout_seconds=timeout,
                open_browser=True
            )
            with open(self.token_file, "w", encoding="utf-8") as f:
                f.write(creds.to_json())
            save_log("INFO", "youtube", "YouTube authorization successful! Token saved for 24/7 automation.")
            profile = self.get_channel_profile()
            return {
                "success": True,
                "profile": profile,
                "message": "유튜브 채널 연동이 성공적으로 완료되었습니다!"
            }
        except Exception as e:
            err_msg = str(e)
            if "timed out" in err_msg.lower() or "timeout" in err_msg.lower():
                err_msg = "로그인 승인 대기 시간이 초과되었거나 사용자가 취소했습니다. 다시 시도해주세요."
            save_log("WARNING", "youtube", f"OAuth authentication stopped: {err_msg}")
            return {"success": False, "error": err_msg}

    def disconnect(self) -> bool:
        """Removes saved token file to disconnect channel."""
        try:
            if self.token_file.exists():
                self.token_file.unlink()
            save_log("INFO", "youtube", "YouTube account disconnected.")
            return True
        except Exception as e:
            save_log("ERROR", "youtube", f"Failed to disconnect YouTube account: {e}")
            return False


    def upload_short(
        self,
        video_path: str,
        title: str,
        description: str,
        tags: Optional[List[str]] = None,
        privacy_status: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Uploads a 9:16 vertical video as YouTube Shorts:
        - Ensures '#shorts' tag in title
        - Sets video category (22: People & Blogs)
        - Uploads using resumable media uploader
        """
        path = Path(video_path)
        if not path.exists():
            return {"success": False, "error": f"Video file not found: {video_path}"}

        # Format title (YouTube max 100 chars, must include #shorts)
        if "#shorts" not in title.lower():
            title = f"{title[:88]} #shorts"
        else:
            title = title[:100]

        tags = tags or ["shorts", "쿠팡", "내돈내산", "꿀템", "쇼츠"]
        privacy = privacy_status or self.privacy_status

        # Simulation Mode or Missing Credentials
        if self.simulation_mode or not self.has_credentials():
            save_log(
                "INFO", "youtube",
                f"[유튜브 시뮬레이션 모드] 영상 업로드 준비 완료: '{title}' (client_secrets.json 등록 시 자동 송출)"
            )
            sim_id = f"sim_yt_{int(time.time())}"
            return {
                "success": True,
                "simulated": True,
                "video_id": sim_id,
                "url": f"https://youtube.com/shorts/{sim_id}",
                "title": title,
                "privacy": privacy,
                "message": "시뮬레이션 모드로 정상 검증되었습니다. (Google OAuth 연동 시 실시간 자동 게시)"
            }

        try:
            save_log("INFO", "youtube", f"Starting YouTube Shorts upload: '{title}' ({path.name})...")
            youtube = self.get_service()

            body = {
                "snippet": {
                    "title": title,
                    "description": description,
                    "tags": tags,
                    "categoryId": "22",  # People & Blogs
                    "defaultLanguage": "ko",
                    "defaultAudioLanguage": "ko"
                },
                "status": {
                    "privacyStatus": privacy,
                    "selfDeclaredMadeForKids": False,
                    "embeddable": True
                }
            }

            media = MediaFileUpload(
                str(path),
                mimetype="video/mp4",
                chunksize=1024 * 1024 * 4,  # 4MB chunks
                resumable=True
            )

            request = youtube.videos().insert(
                part="snippet,status",
                body=body,
                media_body=media
            )

            response = None
            retry_count = 0
            while response is None:
                status, response = request.next_chunk()
                if status:
                    percent = int(status.progress() * 100)
                    save_log("INFO", "youtube", f"Uploading Shorts: {percent}% completed...")

            video_id = response.get("id")
            yt_url = f"https://youtube.com/shorts/{video_id}"
            save_log("INFO", "youtube", f"🎉 YouTube Shorts upload successful! URL: {yt_url}")

            return {
                "success": True,
                "simulated": False,
                "video_id": video_id,
                "url": yt_url,
                "title": title,
                "privacy": privacy
            }

        except Exception as e:
            err_msg = str(e)
            save_log("ERROR", "youtube", f"YouTube upload failed: {err_msg}")
            return {
                "success": False,
                "error": err_msg
            }
