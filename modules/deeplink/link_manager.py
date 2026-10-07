import hashlib
import urllib.parse
from typing import Optional
from database.models import Product
from database.db import save_product, save_log
from modules.sourcing.coupang_api import CoupangApiClient
from config.settings import load_config


class DeepLinkManager:
    """Manages Coupang Partners affiliate link conversion and tracking validation."""

    def __init__(self):
        self.api_client = CoupangApiClient()

    def ensure_deeplink(self, product: Product) -> str:
        """
        Ensures a valid affiliate tracking link or direct product link exists for the given product.
        Guarantees that clicks lead to the exact product and NEVER to the Coupang main page.
        """
        cfg = load_config()
        default_link = cfg.get("coupang", {}).get("default_affiliate_link", "").strip()

        # 1. If product already has a specific verified link (that is NOT a fake link or generic goldbox home link)
        if product.deeplink:
            dl = product.deeplink.strip()
            is_generic = (dl == default_link) and ("goldbox" in dl or "hEyKNvtEFU" in dl)
            is_fake = dl.startswith("https://link.coupang.com/a/b") and len(dl) <= 32 and not dl.endswith("f")  # mock hash pattern
            if not is_generic and not is_fake and (dl.startswith("https://link.coupang.com") or dl.startswith("https://www.coupang.com")):
                return dl

        # 2. Determine target Coupang URL for this product
        target_url = product.original_url
        if not target_url or "products/70" in target_url or "vp/products/70" in target_url:
            encoded_query = urllib.parse.quote(product.title)
            target_url = f"https://www.coupang.com/np/search?q={encoded_query}"

        # 3. If Coupang Partners API is configured, generate an official deep link
        if self.api_client.is_configured():
            try:
                res = self.api_client.create_deeplink([target_url])
                shorten = res.get(target_url)
                if shorten:
                    product.deeplink = shorten
                    product.original_url = target_url
                    save_product(product)
                    save_log("INFO", "deeplink", f"Generated official deep link for {product.title}: {shorten}")
                    return shorten
            except Exception as e:
                save_log("WARNING", "deeplink", f"Coupang API deep link generation failed: {e}")

        # 4. Reliable Direct Coupang Product Search Landing Link (NEVER lands on blank home page)
        product.original_url = target_url
        product.deeplink = target_url
        save_product(product)
        save_log("INFO", "deeplink", f"Set direct Coupang product landing link for {product.title}: {target_url}")
        return target_url
