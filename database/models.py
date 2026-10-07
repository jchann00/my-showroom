from dataclasses import dataclass, field
from typing import Optional, List
from datetime import datetime


@dataclass
class Product:
    product_id: str
    title: str
    price: int
    rating: float
    review_count: int
    is_rocket: bool
    category: str
    original_url: str
    image_url: str
    deeplink: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    posted_at: Optional[str] = None
    status: str = "pending"  # pending, posted, rejected


@dataclass
class PostRecord:
    id: Optional[int] = None
    product_id: Optional[str] = None
    post_type: str = "affiliate"  # 'affiliate' | 'info'
    platform: str = "threads"  # 'threads' | 'instagram' | 'both'
    main_text: str = ""
    comment_1: str = ""
    comment_2: str = ""
    comment_3: str = ""
    image_paths: str = ""  # json or comma-separated
    platform_post_id: Optional[str] = None
    status: str = "pending"  # pending, published, failed, simulated
    scheduled_at: Optional[str] = None
    published_at: Optional[str] = None
    error_msg: Optional[str] = None
