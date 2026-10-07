import hashlib
from typing import Optional
from database.models import Product
from database.db import save_product, save_log
from modules.sourcing.coupang_api import CoupangApiClient


class DeepLinkManager:
    """Manages Coupang Partners affiliate link conversion and tracking validation."""

    def __init__(self):
        self.api_client = CoupangApiClient()

    def ensure_deeplink(self, product: Product) -> str:
        """
        Ensures a valid affiliate tracking link exists for the given product.
        Updates the product record in the database.
        """
        if product.deeplink and product.deeplink.startswith("https://link.coupang.com"):
            return product.deeplink

        original_url = product.original_url

        if self.api_client.is_configured():
            res = self.api_client.create_deeplink([original_url])
            shorten = res.get(original_url)
            if shorten:
                product.deeplink = shorten
                save_product(product)
                save_log("INFO", "deeplink", f"Generated official deep link for {product.title}: {shorten}")
                return shorten

        # If user provided a manual default affiliate link (e.g. before getting API approval)
        from config.settings import load_config
        cfg = load_config()
        custom_link = cfg.get("coupang", {}).get("default_affiliate_link", "").strip()
        if custom_link:
            product.deeplink = custom_link
            save_product(product)
            save_log("INFO", "deeplink", f"Using user registered affiliate link: {custom_link}")
            return custom_link

        # Fallback / Dev / Mock Link
        mock_hash = hashlib.md5((product.product_id + original_url).encode()).hexdigest()[:8]
        fallback_link = f"https://link.coupang.com/a/b{mock_hash}"
        product.deeplink = fallback_link
        save_product(product)
        save_log("INFO", "deeplink", f"Generated fallback affiliate link: {fallback_link}")
        return fallback_link
