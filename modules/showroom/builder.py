import json
from pathlib import Path
from typing import List, Dict, Any
from config.settings import BASE_DIR, load_config
from database.db import get_recent_products

SHOWROOM_DIR = BASE_DIR / "showroom"
SHOWROOM_HTML_PATH = SHOWROOM_DIR / "index.html"


class ShowroomBuilder:
    """Builds and maintains the zero-touch mobile showroom/catalog web page."""

    @classmethod
    def build_showroom_html(cls) -> str:
        """Generates a standalone, mobile-responsive HTML showroom file."""
        cfg = load_config()
        default_link = cfg.get("coupang", {}).get("default_affiliate_link", "https://link.coupang.com/a/hEyKNvtEFU")
        products = get_recent_products(limit=100)

        # Build product items HTML
        items_html = ""
        for idx, p in enumerate(products, start=1):
            target_link = p.get("deeplink") or default_link
            img_url = p.get("image_url") or "https://images.unsplash.com/photo-1584820927498-cfe5211fd8bf?w=800"
            price_formatted = f"{p.get('price', 0):,}원"
            rating = p.get("rating", 4.5)
            reviews = f"{p.get('review_count', 1000):,}개"
            category = p.get("category", "생활용품")

            items_html += f"""
        <div class="product-card" data-category="{category}">
          <div class="card-badge">#{idx} 영상 속 꿀템</div>
          <div class="img-wrapper">
            <img src="{img_url}" alt="{p.get('title')}" loading="lazy">
          </div>
          <div class="card-content">
            <div class="category-tag">{category}</div>
            <h3 class="product-title">{p.get('title')}</h3>
            <div class="price-row">
              <span class="price-val">{price_formatted}</span>
              <span class="rocket-badge">⚡ 로켓배송</span>
            </div>
            <div class="review-row">
              <span class="star">★</span> {rating} ({reviews} 리뷰)
            </div>
            <a href="{target_link}" target="_blank" rel="noopener noreferrer" class="btn-buy">
              👉 쿠팡 최저가 보러가기
            </a>
          </div>
        </div>
            """

        html_content = f"""<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
  <title>꿀템 아카이브 | 숏츠 속 실사용 꿀템 모음</title>
  <style>
    :root {{
      --bg: #0F172A;
      --card-bg: #1E293B;
      --accent: #38BDF8;
      --btn-grad: linear-gradient(135deg, #0284C7, #2563EB);
      --text: #F8FAFC;
      --text-muted: #94A3B8;
    }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      background: var(--bg);
      color: var(--text);
      font-family: -apple-system, BlinkMacSystemFont, "Pretendard", "Segoe UI", Roboto, sans-serif;
      line-height: 1.5;
      padding-bottom: 60px;
    }}
    .header {{
      background: rgba(15, 23, 42, 0.95);
      backdrop-filter: blur(10px);
      position: sticky;
      top: 0;
      z-index: 100;
      border-bottom: 1px solid rgba(255, 255, 255, 0.08);
      padding: 16px 20px;
      text-align: center;
    }}
    .header h1 {{
      font-size: 18px;
      font-weight: 700;
      letter-spacing: -0.5px;
    }}
    .header p {{
      font-size: 12px;
      color: var(--text-muted);
      margin-top: 4px;
    }}
    .container {{
      max-width: 540px;
      margin: 0 auto;
      padding: 16px;
    }}
    .filter-bar {{
      display: flex;
      gap: 8px;
      overflow-x: auto;
      padding-bottom: 12px;
      scrollbar-width: none;
    }}
    .filter-btn {{
      background: rgba(255, 255, 255, 0.06);
      border: 1px solid rgba(255, 255, 255, 0.1);
      color: var(--text-muted);
      padding: 6px 14px;
      border-radius: 20px;
      font-size: 12.5px;
      cursor: pointer;
      white-space: nowrap;
      transition: all 0.2s;
    }}
    .filter-btn.active {{
      background: #2563EB;
      color: #fff;
      border-color: #2563EB;
      font-weight: 600;
    }}
    .product-list {{
      display: flex;
      flex-direction: column;
      gap: 16px;
      margin-top: 8px;
    }}
    .product-card {{
      background: var(--card-bg);
      border: 1px solid rgba(255, 255, 255, 0.08);
      border-radius: 16px;
      overflow: hidden;
      display: flex;
      position: relative;
      box-shadow: 0 4px 16px rgba(0, 0, 0, 0.3);
    }}
    .card-badge {{
      position: absolute;
      top: 10px;
      left: 10px;
      background: #E11D48;
      color: #fff;
      font-size: 11px;
      font-weight: 700;
      padding: 3px 8px;
      border-radius: 6px;
      z-index: 2;
    }}
    .img-wrapper {{
      width: 130px;
      min-width: 130px;
      height: 150px;
      background: #0B1120;
    }}
    .img-wrapper img {{
      width: 100%;
      height: 100%;
      object-fit: cover;
    }}
    .card-content {{
      padding: 12px 14px;
      flex: 1;
      display: flex;
      flex-direction: column;
      justify-content: space-between;
    }}
    .category-tag {{
      font-size: 11px;
      color: var(--accent);
      font-weight: 600;
      margin-bottom: 2px;
    }}
    .product-title {{
      font-size: 13.5px;
      font-weight: 600;
      line-height: 1.4;
      display: -webkit-box;
      -webkit-line-clamp: 2;
      -webkit-box-orient: vertical;
      overflow: hidden;
    }}
    .price-row {{
      display: flex;
      align-items: center;
      gap: 8px;
      margin-top: 6px;
    }}
    .price-val {{
      font-size: 16px;
      font-weight: 700;
      color: #38BDF8;
    }}
    .rocket-badge {{
      font-size: 11px;
      background: rgba(37, 99, 235, 0.2);
      color: #60A5FA;
      padding: 2px 6px;
      border-radius: 4px;
      font-weight: 600;
    }}
    .review-row {{
      font-size: 11.5px;
      color: var(--text-muted);
      margin-top: 2px;
    }}
    .star {{ color: #FBBF24; }}
    .btn-buy {{
      margin-top: 8px;
      background: var(--btn-grad);
      color: #fff;
      text-decoration: none;
      padding: 8px 12px;
      border-radius: 8px;
      font-size: 12.5px;
      font-weight: 700;
      text-align: center;
      display: block;
      transition: opacity 0.2s;
    }}
    .btn-buy:active {{ opacity: 0.8; }}
    .footer-ftc {{
      margin-top: 32px;
      padding: 16px;
      background: rgba(255, 255, 255, 0.03);
      border-radius: 12px;
      font-size: 11px;
      color: #64748B;
      text-align: center;
      line-height: 1.6;
    }}
  </style>
</head>
<body>
  <header class="header">
    <h1>✨ 꿀템 아카이브</h1>
    <p>쇼츠 영상 속 번호를 확인하고 최저가로 만나보세요!</p>
  </header>

  <main class="container">
    <div class="filter-bar">
      <button class="filter-btn active" data-filter="all">전체보기</button>
      <button class="filter-btn" data-filter="생활용품">생활용품</button>
      <button class="filter-btn" data-filter="아이디어">아이디어/데스크</button>
      <button class="filter-btn" data-filter="펫상품">반려동물</button>
      <button class="filter-btn" data-filter="다이어트">다이어트/식단</button>
    </div>

    <div class="product-list" id="product-list">
      {items_html}
    </div>

    <footer class="footer-ftc">
      본 페이지는 쿠팡 파트너스 활동의 일환으로, 이에 따른 일정액의 수수료를 제공받습니다.<br>
      영상의 제품 번호(#1, #2...)와 일치하는 카드의 버튼을 클릭하시면 쿠팡 공식 상품 페이지로 이동합니다.
    </footer>
  </main>

  <script>
    document.querySelectorAll('.filter-btn').forEach(btn => {{
      btn.addEventListener('click', () => {{
        document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        const filter = btn.getAttribute('data-filter');
        document.querySelectorAll('.product-card').forEach(card => {{
          if (filter === 'all' || card.getAttribute('data-category') === filter) {{
            card.style.display = 'flex';
          }} else {{
            card.style.display = 'none';
          }}
        }});
      }});
    }});
  </script>
</body>
</html>"""

        SHOWROOM_DIR.mkdir(parents=True, exist_ok=True)
        with open(SHOWROOM_HTML_PATH, "w", encoding="utf-8") as f:
            f.write(html_content)

        return html_content
