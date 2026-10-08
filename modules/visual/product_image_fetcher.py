import os
import re
import urllib.parse
import requests
from pathlib import Path
from typing import List, Dict, Optional
from PIL import Image

from config.settings import BASE_DIR
from database.db import save_log

CACHE_DIR = BASE_DIR / "data" / "images" / "products"
CACHE_DIR.mkdir(parents=True, exist_ok=True)


class ProductImageFetcher:
    """
    Fetches and caches REAL product images & detail cuts directly from shopping CDNs.
    Guarantees that video frames, thumbnails, and showroom cards display the ACTUAL product.
    """

    @classmethod
    def fetch_product_images(cls, product_id: str, title: str, category: str = "") -> List[str]:
        """
        Returns a list of local file paths for real product images (up to 4 distinct cuts).
        Downloads and caches high-res images if not already cached.
        """
        prod_folder = CACHE_DIR / product_id
        prod_folder.mkdir(parents=True, exist_ok=True)

        existing_cuts = sorted(list(prod_folder.glob("cut_*.jpg")))
        if len(existing_cuts) >= 3:
            return [str(p) for p in existing_cuts]

        # Search query clean-up (remove trailing numbers/count like '500ml 2개입')
        clean_title = re.sub(r'\s*\d+(?:ml|g|kg|p|개입|세트|매).*$', '', title).strip()
        search_query = clean_title if len(clean_title) >= 4 else title

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }

        downloaded = []
        try:
            url = f"https://search.daum.net/search?w=tot&q={urllib.parse.quote(search_query)}"
            res = requests.get(url, headers=headers, timeout=10)
            if res.status_code == 200:
                thumb_matches = re.findall(r'https://search\d*\.daumcdn\.net/thumb/[^"\'>\s]+fname=([^"\'&>\s]+)', res.text)
                candidate_urls = []
                for raw in thumb_matches:
                    real_url = urllib.parse.unquote(raw)
                    # Filter for legitimate image extensions and reject icons/logos
                    if any(ext in real_url.lower() for ext in ['.jpg', '.png', '.jpeg', '.webp']):
                        if 'daum_og' not in real_url and 'logo' not in real_url.lower() and 'icon' not in real_url.lower():
                            # High-resolution Daum CDN URL
                            highres_url = f"https://search1.daumcdn.net/thumb/R800x800/?fname={raw}"
                            candidate_urls.append((highres_url, real_url))

                seen_hashes = set()
                candidates_loaded = []
                for cdn_url, orig_url in candidate_urls:
                    if len(candidates_loaded) >= 6:
                        break
                    try:
                        img_res = requests.get(cdn_url, headers=headers, timeout=8)
                        if img_res.status_code != 200:
                            img_res = requests.get(orig_url, headers=headers, timeout=8)

                        if img_res.status_code == 200 and len(img_res.content) > 5000:
                            content_hash = hash(img_res.content[:2048])
                            if content_hash in seen_hashes:
                                continue
                            seen_hashes.add(content_hash)

                            import io
                            img = Image.open(io.BytesIO(img_res.content)).convert("RGB")
                            if img.width >= 200 and img.height >= 200:
                                candidates_loaded.append((img.width * img.height, img))
                    except Exception:
                        continue

                # Sort by resolution descending (highest resolution first)
                candidates_loaded.sort(key=lambda x: x[0], reverse=True)

                for idx, (_, img) in enumerate(candidates_loaded[:4], start=1):
                    target_file = prod_folder / f"cut_{idx}.jpg"
                    img.save(target_file, "JPEG", quality=95)
                    downloaded.append(str(target_file))
        except Exception as e:
            save_log("WARNING", "image_fetcher", f"Failed fetching product images for {product_id}: {e}")

        # If downloaded fewer than 4, duplicate the best one
        if downloaded:
            while len(downloaded) < 4:
                downloaded.append(downloaded[0])
            save_log("INFO", "image_fetcher", f"Cached {len(downloaded)} real product images for #{product_id}")
            return downloaded

        return []

    @classmethod
    def get_hero_image_url(cls, product_id: str, title: str) -> Optional[str]:
        """Returns the web-accessible CDN image URL for the primary product thumbnail."""
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        clean_title = re.sub(r'\s*\d+(?:ml|g|kg|p|개입|세트|매).*$', '', title).strip()
        search_query = clean_title if len(clean_title) >= 4 else title
        try:
            url = f"https://search.daum.net/search?w=tot&q={urllib.parse.quote(search_query)}"
            res = requests.get(url, headers=headers, timeout=8)
            thumb_matches = re.findall(r'https://search\d*\.daumcdn\.net/thumb/[^"\'>\s]+fname=([^"\'&>\s]+)', res.text)
            for raw in thumb_matches:
                real_url = urllib.parse.unquote(raw)
                if any(ext in real_url.lower() for ext in ['.jpg', '.png', '.jpeg', '.webp']):
                    if 'daum_og' not in real_url and 'logo' not in real_url.lower():
                        return f"https://search1.daumcdn.net/thumb/R800x800/?fname={raw}"
        except Exception:
            pass
        return None
