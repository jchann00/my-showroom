import hmac
import hashlib
import time
import requests
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from config.settings import load_config
from database.models import Product
from database.db import save_log


class CoupangApiClient:
    DOMAIN = "https://api-gateway.coupang.com"

    def __init__(self, access_key: Optional[str] = None, secret_key: Optional[str] = None):
        cfg = load_config()
        self.access_key = access_key or cfg.get("coupang", {}).get("access_key", "")
        self.secret_key = secret_key or cfg.get("coupang", {}).get("secret_key", "")
        self.sub_id = cfg.get("coupang", {}).get("sub_id", "thread_auto")

    def is_configured(self) -> bool:
        return bool(self.access_key and self.secret_key)

    def _generate_hmac_header(self, method: str, url_path: str, query_string: str = "") -> Dict[str, str]:
        """Generate official Coupang OpenAPI HMAC-SHA256 authorization headers."""
        now_gmt = datetime.now(timezone.utc).strftime("%y%m%d'T'%H%M%S'Z'")
        message = f"{now_gmt}{method.upper()}{url_path}{query_string}"
        
        signature = hmac.new(
            self.secret_key.encode("utf-8"),
            message.encode("utf-8"),
            hashlib.sha256
        ).hexdigest()

        authorization = (
            f"CEA algorithm=HmacSHA256, "
            f"access-key={self.access_key}, "
            f"signed-date={now_gmt}, "
            f"signature={signature}"
        )
        return {
            "Authorization": authorization,
            "Content-Type": "application/json;charset=UTF-8"
        }

    def get_goldbox_products(self) -> List[Dict[str, Any]]:
        """Fetch daily Goldbox deals from Coupang Partners OpenAPI."""
        if not self.is_configured():
            save_log("WARNING", "coupang_api", "Coupang API keys not configured. Skipping OpenAPI call.")
            return []

        path = "/v2/providers/affiliate_open_api/apis/openapi/v1/products/goldbox"
        headers = self._generate_hmac_header("GET", path)

        try:
            res = requests.get(f"{self.DOMAIN}{path}", headers=headers, timeout=10)
            if res.status_code == 200:
                data = res.json()
                items = data.get("data", [])
                save_log("INFO", "coupang_api", f"Fetched {len(items)} items from Coupang Goldbox API.")
                return items
            else:
                save_log("ERROR", "coupang_api", f"Goldbox API error ({res.status_code}): {res.text}")
                return []
        except Exception as e:
            save_log("ERROR", "coupang_api", f"Goldbox API request failed: {e}")
            return []

    def search_products(self, keyword: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search products by keyword."""
        if not self.is_configured():
            return []

        path = "/v2/providers/affiliate_open_api/apis/openapi/v1/products/search"
        query = f"?keyword={keyword}&limit={limit}"
        headers = self._generate_hmac_header("GET", path, query)

        try:
            res = requests.get(f"{self.DOMAIN}{path}{query}", headers=headers, timeout=10)
            if res.status_code == 200:
                data = res.json()
                return data.get("data", {}).get("productData", [])
            else:
                save_log("ERROR", "coupang_api", f"Search API error ({res.status_code}): {res.text}")
                return []
        except Exception as e:
            save_log("ERROR", "coupang_api", f"Search API exception: {e}")
            return []

    def create_deeplink(self, coupang_urls: List[str]) -> Dict[str, str]:
        """Convert regular Coupang URLs into affiliate tracking links."""
        if not self.is_configured():
            save_log("WARNING", "coupang_api", "API key not set. Returning mock tracking links for development/testing.")
            return {url: f"https://link.coupang.com/a/{hashlib.md5(url.encode()).hexdigest()[:6]}" for url in coupang_urls}

        path = "/v2/providers/affiliate_open_api/apis/openapi/v1/deeplink"
        headers = self._generate_hmac_header("POST", path)
        body = {
            "coupangUrls": coupang_urls,
            "subId": self.sub_id
        }

        try:
            res = requests.post(f"{self.DOMAIN}{path}", headers=headers, json=body, timeout=10)
            if res.status_code == 200:
                data = res.json()
                result_map = {}
                for item in data.get("data", []):
                    original = item.get("originalUrl")
                    shorten = item.get("shortenUrl")
                    if original and shorten:
                        result_map[original] = shorten
                return result_map
            else:
                save_log("ERROR", "coupang_api", f"Deeplink API error ({res.status_code}): {res.text}")
                return {}
        except Exception as e:
            save_log("ERROR", "coupang_api", f"Deeplink request failed: {e}")
            return {}
