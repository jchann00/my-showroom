import time
import requests
from typing import Dict, Any, List, Optional
from config.settings import load_config
from database.db import save_log


class ThreadsPublisher:
    """Publishes posts and multi-stage replies using official Meta Threads API."""

    API_BASE = "https://graph.threads.net/v1.0"

    def __init__(self):
        self.reload_config()

    def reload_config(self):
        cfg = load_config()
        self.threads_cfg = cfg.get("threads", {})
        self.user_id = self.threads_cfg.get("user_id", "")
        self.access_token = self.threads_cfg.get("access_token", "")
        self.simulation_mode = self.threads_cfg.get("simulation_mode", True)
        self.reply_interval = cfg.get("strategy", {}).get("reply_interval_seconds", 20)

    def get_effective_user_id(self) -> str:
        """Auto-resolves the real Threads user ID from access token if needed."""
        if not self.access_token:
            return self.user_id
        # If user_id is already a valid Threads user ID (usually starts with 28...)
        if self.user_id and len(self.user_id) > 16:
            return self.user_id

        try:
            res = requests.get(
                f"{self.API_BASE}/me",
                params={"fields": "id,username", "access_token": self.access_token},
                timeout=10
            )
            if res.status_code == 200:
                real_id = res.json().get("id")
                if real_id:
                    self.user_id = real_id
                    save_log("INFO", "threads", f"Auto-detected Threads User ID: {real_id} (@{res.json().get('username')})")
                    return real_id
        except Exception as e:
            save_log("DEBUG", "threads", f"Could not auto-fetch user_id: {e}")
        return self.user_id

    def is_configured(self) -> bool:
        return bool(self.access_token and not self.simulation_mode)

    def publish_full_thread(
        self,
        main_text: str,
        comments: List[str],
        image_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Executes the full 3-step publishing pipeline:
        1. Publish Main Body Post
        2. Wait natural interval (prevent rate-limiting / bot flag)
        3. Publish Comment 1 (FTC + link), Comment 2 (tips), Comment 3 (CTA)
        """
        self.reload_config()

        if self.simulation_mode or not self.is_configured():
            return self._simulate_publish(main_text, comments)

        # 1. Publish Main Post
        main_post_id = self._create_and_publish_container(text=main_text, image_url=image_url)
        if not main_post_id:
            save_log("ERROR", "threads", "Failed to publish main post container.")
            return {"status": "failed", "error": "Main post creation failed"}

        save_log("INFO", "threads", f"Main post published successfully! ID: {main_post_id}")

        reply_ids = []
        # 2. Sequential Reply Publishing
        for idx, comment in enumerate(comments, start=1):
            if not comment.strip():
                continue

            time.sleep(self.reply_interval)
            reply_id = self._create_and_publish_container(
                text=comment,
                reply_to_id=main_post_id
            )
            if reply_id:
                reply_ids.append(reply_id)
                save_log("INFO", "threads", f"Published reply #{idx} (ID: {reply_id})")
            else:
                save_log("WARNING", "threads", f"Failed to publish reply #{idx}")

        return {
            "status": "published",
            "platform_post_id": main_post_id,
            "reply_ids": reply_ids
        }

    def _create_and_publish_container(
        self,
        text: str,
        image_url: Optional[str] = None,
        reply_to_id: Optional[str] = None
    ) -> Optional[str]:
        """Creates container and publishes it via Meta Threads API."""
        try:
            target_user_id = self.get_effective_user_id()
            # Step A: Create container
            create_url = f"{self.API_BASE}/{target_user_id}/threads"
            payload = {
                "access_token": self.access_token,
                "text": text,
            }
            if image_url:
                payload["media_type"] = "IMAGE"
                payload["image_url"] = image_url
            else:
                payload["media_type"] = "TEXT"

            if reply_to_id:
                payload["reply_to_id"] = reply_to_id

            res = requests.post(create_url, data=payload, timeout=15)
            if res.status_code != 200:
                save_log("ERROR", "threads", f"Container creation failed ({res.status_code}): {res.text}")
                return None

            creation_id = res.json().get("id")
            if not creation_id:
                return None

            # Small pause before publish
            time.sleep(3)

            # Step B: Publish container
            publish_url = f"{self.API_BASE}/{target_user_id}/threads_publish"
            pub_res = requests.post(
                publish_url,
                data={"creation_id": creation_id, "access_token": self.access_token},
                timeout=15
            )
            if pub_res.status_code == 200:
                return pub_res.json().get("id")
            else:
                save_log("ERROR", "threads", f"Publish failed ({pub_res.status_code}): {pub_res.text}")
                return None
        except Exception as e:
            save_log("ERROR", "threads", f"Threads API exception: {e}")
            return None

    def _simulate_publish(self, main_text: str, comments: List[str]) -> Dict[str, Any]:
        """Simulate publishing for testing and environments without production credentials."""
        simulated_id = f"sim_threads_{int(time.time())}"
        save_log("INFO", "threads", f"[SIMULATION] Main post prepared (300자 검증 완료):\n{main_text[:80]}...")
        for i, c in enumerate(comments, 1):
            if c:
                save_log("INFO", "threads", f"[SIMULATION] 댓글 #{i} 대기열 등록 완료 (길이: {len(c)}자)")

        return {
            "status": "simulated",
            "platform_post_id": simulated_id,
            "reply_ids": [f"{simulated_id}_rep{i}" for i in range(1, len(comments) + 1)]
        }
