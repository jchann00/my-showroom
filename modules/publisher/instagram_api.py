import time
import requests
from typing import Dict, Any, List, Optional
from config.settings import load_config
from database.db import save_log


class InstagramPublisher:
    """Publishes carousel/photo posts and first-comment links to Instagram Graph API."""

    API_BASE = "https://graph.facebook.com/v20.0"

    def __init__(self):
        self.reload_config()

    def reload_config(self):
        cfg = load_config()
        self.ig_cfg = cfg.get("instagram", {})
        self.user_id = self.ig_cfg.get("user_id", "")
        self.access_token = self.ig_cfg.get("access_token", "")
        self.simulation_mode = self.ig_cfg.get("simulation_mode", True)

    def is_configured(self) -> bool:
        return bool(self.user_id and self.access_token and not self.simulation_mode)

    def publish_post(
        self,
        image_url: str,
        caption: str,
        comment_1: Optional[str] = None
    ) -> Dict[str, Any]:
        """Publish image post and comment 1 to Instagram."""
        self.reload_config()

        if self.simulation_mode or not self.is_configured():
            sim_id = f"sim_ig_{int(time.time())}"
            save_log("INFO", "instagram", f"[SIMULATION] IG Post prepared with image: {image_url}")
            return {"status": "simulated", "platform_post_id": sim_id}

        try:
            # 1. Create Media Container
            container_url = f"{self.API_BASE}/{self.user_id}/media"
            res = requests.post(
                container_url,
                data={
                    "image_url": image_url,
                    "caption": caption,
                    "access_token": self.access_token
                },
                timeout=20
            )
            if res.status_code != 200:
                save_log("ERROR", "instagram", f"Media upload failed: {res.text}")
                return {"status": "failed", "error": res.text}

            creation_id = res.json().get("id")
            time.sleep(5)

            # 2. Publish Media
            publish_url = f"{self.API_BASE}/{self.user_id}/media_publish"
            pub_res = requests.post(
                publish_url,
                data={"creation_id": creation_id, "access_token": self.access_token},
                timeout=20
            )
            if pub_res.status_code != 200:
                save_log("ERROR", "instagram", f"Publish failed: {pub_res.text}")
                return {"status": "failed", "error": pub_res.text}

            media_id = pub_res.json().get("id")

            # 3. Post Comment 1 (FTC + link)
            if comment_1 and media_id:
                time.sleep(5)
                comment_url = f"{self.API_BASE}/{media_id}/comments"
                requests.post(
                    comment_url,
                    data={"message": comment_1, "access_token": self.access_token},
                    timeout=15
                )

            return {"status": "published", "platform_post_id": media_id}
        except Exception as e:
            save_log("ERROR", "instagram", f"Instagram API exception: {e}")
            return {"status": "failed", "error": str(e)}
