import os
import json
from pathlib import Path
from typing import Dict, Any
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
CONFIG_FILE = BASE_DIR / "config" / "user_config.json"
DEFAULT_CONFIG_FILE = BASE_DIR / "config" / "default_config.json"
DATA_DIR = BASE_DIR / "data"
IMAGE_DIR = DATA_DIR / "images"
LOG_DIR = DATA_DIR / "logs"
DB_PATH = DATA_DIR / "automation.db"

# Load .env if present
load_dotenv(BASE_DIR / ".env")


def load_config() -> Dict[str, Any]:
    """Load configuration with fallback to default_config.json and environment variables."""
    # Ensure directories exist
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    IMAGE_DIR.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    config = {}
    if DEFAULT_CONFIG_FILE.exists():
        with open(DEFAULT_CONFIG_FILE, "r", encoding="utf-8") as f:
            config = json.load(f)

    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            user_cfg = json.load(f)
            # Deep merge
            for section, values in user_cfg.items():
                if section in config and isinstance(values, dict):
                    config[section].update(values)
                else:
                    config[section] = values

    # Override from environment variables if present
    if os.getenv("COUPANG_ACCESS_KEY"):
        config["coupang"]["access_key"] = os.getenv("COUPANG_ACCESS_KEY")
    if os.getenv("COUPANG_SECRET_KEY"):
        config["coupang"]["secret_key"] = os.getenv("COUPANG_SECRET_KEY")
    if os.getenv("COUPANG_SUB_ID"):
        config["coupang"]["sub_id"] = os.getenv("COUPANG_SUB_ID")

    if os.getenv("GEMINI_API_KEY"):
        config["llm"]["gemini_api_key"] = os.getenv("GEMINI_API_KEY")
    if os.getenv("OPENAI_API_KEY"):
        config["llm"]["openai_api_key"] = os.getenv("OPENAI_API_KEY")
    if os.getenv("CLAUDE_API_KEY"):
        config["llm"]["claude_api_key"] = os.getenv("CLAUDE_API_KEY")

    if os.getenv("THREADS_ACCESS_TOKEN"):
        config["threads"]["access_token"] = os.getenv("THREADS_ACCESS_TOKEN")
    if os.getenv("THREADS_USER_ID"):
        config["threads"]["user_id"] = os.getenv("THREADS_USER_ID")

    if os.getenv("INSTAGRAM_ACCESS_TOKEN"):
        config["instagram"]["access_token"] = os.getenv("INSTAGRAM_ACCESS_TOKEN")
    if os.getenv("INSTAGRAM_USER_ID"):
        config["instagram"]["user_id"] = os.getenv("INSTAGRAM_USER_ID")

    if os.getenv("DISCORD_WEBHOOK"):
        config["notifications"]["discord_webhook"] = os.getenv("DISCORD_WEBHOOK")
    if os.getenv("TELEGRAM_BOT_TOKEN"):
        config["notifications"]["telegram_bot_token"] = os.getenv("TELEGRAM_BOT_TOKEN")
    if os.getenv("TELEGRAM_CHAT_ID"):
        config["notifications"]["telegram_chat_id"] = os.getenv("TELEGRAM_CHAT_ID")

    return config


def save_config(updated_config: Dict[str, Any]) -> None:
    """Save user modified configuration."""
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(updated_config, f, ensure_ascii=False, indent=2)


# Initial load
CONFIG = load_config()
