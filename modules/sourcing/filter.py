from typing import Dict, Any, Tuple
from config.settings import load_config
from database.models import Product


def filter_product(product: Product) -> Tuple[bool, str]:
    """
    Check if a product meets all monetization & conversion criteria.
    Criteria:
    - Price: 10,000 KRW <= price <= 39,900 KRW (prevents high-ticket drop-off)
    - Rating: >= 4.5
    - Review count: >= 1,000
    - Rocket Delivery: is_rocket == True
    """
    cfg = load_config()
    filters = cfg.get("filters", {})

    min_price = filters.get("min_price", 10000)
    max_price = filters.get("max_price", 39900)
    min_rating = filters.get("min_rating", 4.5)
    min_reviews = filters.get("min_reviews", 1000)
    require_rocket = filters.get("require_rocket", True)

    if product.price < min_price:
        return False, f"가격 미달 ({product.price:,}원 < {min_price:,}원)"

    if product.price > max_price:
        return False, f"가격 초과 ({product.price:,}원 > {max_price:,}원 - 이탈 방지)"

    if product.rating < min_rating:
        return False, f"평점 부족 ({product.rating} < {min_rating})"

    if product.review_count < min_reviews:
        return False, f"리뷰 수 부족 ({product.review_count:,}개 < {min_reviews:,}개)"

    if require_rocket and not product.is_rocket:
        return False, "로켓배송 미지원"

    return True, "조건 충족 (통과)"
