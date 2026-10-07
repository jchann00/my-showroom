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
        """Generates a standalone, mobile-responsive HTML showroom file synchronized with Shorts."""
        import urllib.parse
        cfg = load_config()
        products = get_recent_products(limit=100)

        # Build product items HTML
        items_html = ""
        for p in products:
            s_num = p.get("showroom_num", 1)
            raw_title = p.get("title", "")
            target_link = p.get("deeplink")
            if not target_link or "products/70" in target_link or "vp/products/70" in target_link or "hEyKNvtEFU" in target_link:
                target_link = f"https://www.coupang.com/np/search?q={urllib.parse.quote(raw_title)}"

            img_url = p.get("image_url") or "https://images.unsplash.com/photo-1584820927498-cfe5211fd8bf?w=800"
            price_formatted = f"{p.get('price', 0):,}원"
            rating = p.get("rating", 4.5)
            reviews = f"{p.get('review_count', 1000):,}개"
            category = p.get("category", "생활용품")
            is_posted = p.get("status") == "posted"

            badge_text = f"🔥 #{s_num} 영상 방영 꿀템" if is_posted else f"#{s_num} 추천 꿀템"
            badge_class = "card-badge featured" if is_posted else "card-badge"

            items_html += f"""
        <div class="product-card" id="card-{s_num}" data-num="{s_num}" data-category="{category}">
          <div class="{badge_class}">{badge_text}</div>
          <div class="img-wrapper">
            <img src="{img_url}" alt="{raw_title}" loading="lazy">
          </div>
          <div class="card-content">
            <div class="category-tag">{category}</div>
            <h3 class="product-title">{raw_title}</h3>
            <div class="price-row">
              <span class="price-val">{price_formatted}</span>
              <span class="rocket-badge">⚡ 로켓배송</span>
            </div>
            <div class="review-row">
              <span class="star">★</span> {rating} ({reviews} 리뷰)
            </div>
            <a href="{target_link}" target="_blank" rel="noopener noreferrer" class="btn-buy" id="buy-btn-{s_num}">
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
  <title>꿀템 쇼룸 | 숏츠 영상 속 번호 맞춤 꿀템 모음</title>
  <style>
    :root {{
      --bg: #0F172A;
      --card-bg: #1E293B;
      --accent: #38BDF8;
      --btn-grad: linear-gradient(135deg, #E11D48, #BE123C);
      --btn-buy: linear-gradient(135deg, #0284C7, #2563EB);
      --text: #F8FAFC;
      --text-muted: #94A3B8;
    }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      background: var(--bg);
      color: var(--text);
      font-family: -apple-system, BlinkMacSystemFont, "Pretendard", "Segoe UI", Roboto, sans-serif;
      line-height: 1.5;
      padding-bottom: 70px;
    }}
    .header {{
      background: rgba(15, 23, 42, 0.95);
      backdrop-filter: blur(12px);
      position: sticky;
      top: 0;
      z-index: 100;
      border-bottom: 1px solid rgba(255, 255, 255, 0.08);
      padding: 16px 20px;
      text-align: center;
    }}
    .header h1 {{
      font-size: 19px;
      font-weight: 800;
      letter-spacing: -0.5px;
      background: linear-gradient(135deg, #38BDF8, #818CF8);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
    }}
    .header p {{
      font-size: 12.5px;
      color: var(--text-muted);
      margin-top: 4px;
    }}
    .container {{
      max-width: 540px;
      margin: 0 auto;
      padding: 16px;
    }}
    /* Quick Jump Search Box */
    .search-box {{
      display: flex;
      gap: 8px;
      margin-bottom: 14px;
      background: rgba(255, 255, 255, 0.04);
      padding: 8px;
      border-radius: 14px;
      border: 1px solid rgba(255, 255, 255, 0.08);
    }}
    .search-box input {{
      flex: 1;
      background: rgba(0, 0, 0, 0.3);
      border: 1px solid rgba(255, 255, 255, 0.12);
      border-radius: 10px;
      padding: 10px 14px;
      font-size: 13.5px;
      color: #fff;
      outline: none;
    }}
    .search-box input:focus {{
      border-color: #38BDF8;
    }}
    .search-box button {{
      background: var(--btn-buy);
      border: none;
      color: #fff;
      font-weight: 700;
      padding: 0 16px;
      border-radius: 10px;
      cursor: pointer;
      font-size: 13px;
      white-space: nowrap;
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
      margin-top: 4px;
    }}
    .product-card {{
      background: var(--card-bg);
      border: 1px solid rgba(255, 255, 255, 0.08);
      border-radius: 16px;
      overflow: hidden;
      display: flex;
      position: relative;
      box-shadow: 0 4px 16px rgba(0, 0, 0, 0.3);
      transition: transform 0.2s, border-color 0.3s, box-shadow 0.3s;
    }}
    .product-card.highlight {{
      border-color: #38BDF8;
      box-shadow: 0 0 20px rgba(56, 189, 248, 0.4);
      transform: scale(1.02);
    }}
    .card-badge {{
      position: absolute;
      top: 10px;
      left: 10px;
      background: rgba(30, 41, 59, 0.85);
      border: 1px solid rgba(255, 255, 255, 0.2);
      backdrop-filter: blur(4px);
      color: #E2E8F0;
      font-size: 11px;
      font-weight: 700;
      padding: 3px 8px;
      border-radius: 6px;
      z-index: 2;
    }}
    .card-badge.featured {{
      background: #E11D48;
      border: none;
      color: #fff;
      box-shadow: 0 2px 8px rgba(225, 29, 72, 0.5);
    }}
    .img-wrapper {{
      width: 130px;
      min-width: 130px;
      height: 155px;
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
      background: var(--btn-buy);
      color: #fff;
      text-decoration: none;
      padding: 9px 12px;
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
    <h1>✨ 꿀템 쇼룸 아카이브</h1>
    <p>쇼츠 영상 속 번호(#1, #2...)와 일치하는 상품을 확인하세요!</p>
  </header>

  <main class="container">
    <!-- Quick Number Jump -->
    <div class="search-box">
      <input type="number" id="quick-num-input" placeholder="영상 속 상품 번호 입력 (예: 5)" min="1">
      <button id="btn-jump-num">바로 찾기</button>
    </div>

    <!-- Category Filter Bar -->
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
      영상의 제품 번호(#1, #2...)와 일치하는 카드의 버튼을 클릭하시면 쿠팡 공식 상품 페이지로 안전하게 이동합니다.
    </footer>
  </main>

  <script>
    // Category Filter
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

    // Quick Jump by Item Number
    function jumpToNumber() {{
      const num = document.getElementById('quick-num-input').value.trim();
      if (!num) return;
      const targetCard = document.getElementById('card-' + num);
      if (targetCard) {{
        // Reset category filter if needed
        document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
        document.querySelector('[data-filter=all]').classList.add('active');
        document.querySelectorAll('.product-card').forEach(c => c.style.display = 'flex');

        targetCard.scrollIntoView({{ behavior: 'smooth', block: 'center' }});
        targetCard.classList.add('highlight');
        setTimeout(() => targetCard.classList.remove('highlight'), 2000);
      }} else {{
        alert('#' + num + '번 상품을 찾을 수 없습니다.');
      }}
    }}

    document.getElementById('btn-jump-num').addEventListener('click', jumpToNumber);
    document.getElementById('quick-num-input').addEventListener('keypress', (e) => {{
      if (e.key === 'Enter') jumpToNumber();
    }});
  </script>
</body>
</html>"""

        SHOWROOM_DIR.mkdir(parents=True, exist_ok=True)
        with open(SHOWROOM_HTML_PATH, "w", encoding="utf-8") as f:
            f.write(html_content)

        # Also write to docs/index.html for 1-click GitHub Pages deployment
        docs_dir = BASE_DIR / "docs"
        docs_dir.mkdir(parents=True, exist_ok=True)
        with open(docs_dir / "index.html", "w", encoding="utf-8") as f:
            f.write(html_content)

        return html_content

    @classmethod
    def get_showroom_url(cls) -> str:
        """Returns the public showroom URL if configured, or default localhost URL."""
        cfg = load_config()
        public_url = cfg.get("showroom", {}).get("public_url", "").strip()
        if public_url:
            return public_url
        return "http://127.0.0.1:8080/showroom"
