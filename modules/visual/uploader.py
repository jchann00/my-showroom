import os
import requests
from pathlib import Path
from typing import Optional
from database.db import save_log


class ImageUploader:
    """
    Uploads locally generated card images to a public CDN/host
    so Meta Graph API (Threads / Instagram) can fetch and attach them to posts.
    Uses free, keyless public image endpoints (Catbox / Litterbox) with instant response.
    """

    CATBOX_API = "https://catbox.moe/user/api.php"

    @classmethod
    def upload_image(cls, file_path: str) -> Optional[str]:
        """Uploads a local image file and returns a public HTTPS URL."""
        if not os.path.exists(file_path):
            return None

        try:
            with open(file_path, "rb") as f:
                files = {"fileToUpload": f}
                data = {"reqtype": "fileupload"}
                res = requests.post(cls.CATBOX_API, data=data, files=files, timeout=15)

            if res.status_code == 200 and res.text.startswith("https://"):
                public_url = res.text.strip()
                save_log("INFO", "uploader", f"Uploaded card image to public CDN: {public_url}")
                return public_url
            else:
                save_log("DEBUG", "uploader", f"Public image upload failed: {res.text}")
                return None
        except Exception as e:
            save_log("DEBUG", "uploader", f"Image upload exception: {e}")
            return None
