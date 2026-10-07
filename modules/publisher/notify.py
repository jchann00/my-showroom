import requests
from config.settings import load_config
from database.db import save_log


class NotificationManager:
    """Sends webhook alerts to Discord or Telegram when posts are scheduled or published."""

    def __init__(self):
        self.reload_config()

    def reload_config(self):
        cfg = load_config()
        self.notif_cfg = cfg.get("notifications", {})
        self.discord_url = self.notif_cfg.get("discord_webhook", "")
        self.telegram_token = self.notif_cfg.get("telegram_bot_token", "")
        self.telegram_chat_id = self.notif_cfg.get("telegram_chat_id", "")

    def send_post_alert(self, title: str, category: str, price: int, deeplink: str, status: str):
        self.reload_config()
        text = (
            f"🚀 [쓰레드/인스타 자동 발행 완료]\n"
            f"• 상품명: {title}\n"
            f"• 카테고리: {category} | 가격: {price:,}원\n"
            f"• 파트너스 링크: {deeplink}\n"
            f"• 상태: {status}"
        )

        if self.discord_url:
            try:
                requests.post(self.discord_url, json={"content": text}, timeout=5)
            except Exception as e:
                save_log("DEBUG", "notify", f"Discord notification failed: {e}")

        if self.telegram_token and self.telegram_chat_id:
            try:
                tg_url = f"https://api.telegram.org/bot{self.telegram_token}/sendMessage"
                requests.post(tg_url, json={"chat_id": self.telegram_chat_id, "text": text}, timeout=5)
            except Exception as e:
                save_log("DEBUG", "notify", f"Telegram notification failed: {e}")
