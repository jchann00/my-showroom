import io
import os
import requests
from pathlib import Path
from typing import List, Optional
from PIL import Image, ImageDraw, ImageFont
from config.settings import IMAGE_DIR
from database.db import save_log

# Font paths on Windows
FONT_BOLD_PATH = "C:\\Windows\\Fonts\\malgunbd.ttf"
FONT_REGULAR_PATH = "C:\\Windows\\Fonts\\malgun.ttf"


class CardGenerator:
    """Generates high-converting 1080x1080 card news and thumbnails for Instagram & Threads."""

    def __init__(self):
        self.output_dir = IMAGE_DIR
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.width = 1080
        self.height = 1080

    def _get_font(self, size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
        font_file = FONT_BOLD_PATH if bold else FONT_REGULAR_PATH
        if os.path.exists(font_file):
            return ImageFont.truetype(font_file, size)
        try:
            return ImageFont.truetype("arial.ttf", size)
        except Exception:
            return ImageFont.load_default()

    def generate_cards(
        self,
        product_id: str,
        headline: str,
        subtext: str,
        category: str,
        price: int,
        rating: float,
        review_count: int,
        image_url: Optional[str] = None
    ) -> List[str]:
        """
        Generates 2 aesthetic card news slides:
        - Slide 1: High-converting Hook Cover Card
        - Slide 2: Real Specification & Comment Guide Card
        Returns paths to generated image files.
        """
        paths = []
        slide1_path = self._generate_cover_card(
            product_id, headline, subtext, category, price, rating, review_count, image_url
        )
        paths.append(str(slide1_path))

        slide2_path = self._generate_detail_card(
            product_id, headline, category, price, rating, review_count
        )
        paths.append(str(slide2_path))

        return paths

    def _generate_cover_card(
        self,
        product_id: str,
        headline: str,
        subtext: str,
        category: str,
        price: int,
        rating: float,
        review_count: int,
        image_url: Optional[str]
    ) -> Path:
        """Slide 1: Viral Hook Cover Card."""
        img = Image.new("RGB", (self.width, self.height), color="#0F172A")  # Modern slate dark background
        draw = ImageDraw.Draw(img)

        # Subtle gradient / accent glow on top
        for y in range(260):
            alpha = int(255 * (1 - y / 260))
            draw.line([(0, y), (self.width, y)], fill=(30, 41, 59))

        # Top Category Tag Pill
        tag_text = f"BEST · {category} 찐후기"
        tag_font = self._get_font(26, bold=True)
        tag_w = draw.textlength(tag_text, font=tag_font)
        draw.rounded_rectangle((80, 80, 80 + tag_w + 40, 136), radius=10, fill="#E11D48")
        draw.text((100, 93), tag_text, font=tag_font, fill="#FFFFFF")

        # Rocket delivery pill
        rocket_text = "ROCKET · 로켓배송"
        rocket_font = self._get_font(26, bold=True)
        rocket_w = draw.textlength(rocket_text, font=rocket_font)
        rx = 80 + tag_w + 55
        draw.rounded_rectangle((rx, 80, rx + rocket_w + 40, 136), radius=10, fill="#2563EB")
        draw.text((rx + 20, 93), rocket_text, font=rocket_font, fill="#FFFFFF")

        # Headline
        head_font = self._get_font(56, bold=True)
        wrapped_headline = self._wrap_text(headline, 16)
        y_pos = 180
        for line in wrapped_headline.split("\n"):
            draw.text((80, y_pos), line, font=head_font, fill="#F8FAFC")
            y_pos += 72

        # Subtext
        sub_font = self._get_font(34, bold=False)
        draw.text((80, y_pos + 10), subtext, font=sub_font, fill="#94A3B8")

        # Product Image Area (Center Card)
        card_rect = (80, 440, 1000, 900)
        draw.rounded_rectangle(card_rect, radius=24, fill="#1E293B", outline="#334155", width=2)

        # Download & Paste Product Image
        product_img = self._load_product_image(image_url)
        if product_img:
            # Resize preserving aspect ratio
            product_img.thumbnail((400, 400), Image.Resampling.LANCZOS)
            px = 120 + (400 - product_img.width) // 2
            py = 470 + (400 - product_img.height) // 2
            img.paste(product_img, (px, py))
        else:
            # Fallback illustration placeholder
            draw.rounded_rectangle((120, 470, 500, 850), radius=16, fill="#0F172A")
            draw.text((220, 640), "📦 BEST", font=self._get_font(48, bold=True), fill="#64748B")

        # Right side info in card
        info_x = 560
        price_tag_font = self._get_font(30, bold=False)
        draw.text((info_x, 520), "쿠팡 할인가", font=price_tag_font, fill="#94A3B8")

        price_num_font = self._get_font(54, bold=True)
        draw.text((info_x, 565), f"{price:,}원", font=price_num_font, fill="#38BDF8")

        rate_font = self._get_font(32, bold=True)
        draw.text((info_x, 650), f"★ {rating}점", font=rate_font, fill="#FBBF24")
        draw.text((info_x + 130, 650), f"({review_count:,}개 리뷰)", font=self._get_font(28), fill="#94A3B8")

        status_font = self._get_font(28, bold=True)
        draw.text((info_x, 725), "● 내일 아침 도착 보장", font=status_font, fill="#4ADE80")

        # Bottom Bar: CTA
        draw.rounded_rectangle((80, 940, 1000, 1020), radius=16, fill="#2563EB")
        cta_font = self._get_font(32, bold=True)
        cta_text = "▶ 제품 링크 & 실사용 팁은 댓글에 남겨둘게요!"
        draw.text((160, 962), cta_text, font=cta_font, fill="#FFFFFF")

        file_path = self.output_dir / f"{product_id}_slide1.png"
        img.save(file_path, quality=95)
        return file_path

    def _generate_detail_card(
        self,
        product_id: str,
        headline: str,
        category: str,
        price: int,
        rating: float,
        review_count: int
    ) -> Path:
        """Slide 2: 3-point check card."""
        img = Image.new("RGB", (self.width, self.height), color="#0F172A")
        draw = ImageDraw.Draw(img)

        # Header
        draw.text((80, 80), f"CHECK · {category} 꿀팁 정리", font=self._get_font(36, bold=True), fill="#38BDF8")
        draw.text((80, 140), "구매 전 꼭 체크할 3가지", font=self._get_font(56, bold=True), fill="#F8FAFC")

        # 3 Points Box
        points = [
            ("1. 가격 메리트", f"1~3만 원대({price:,}원)로 부담 없는 갓성비"),
            ("2. 검증된 후기", f"리뷰 {review_count:,}개 / 평점 {rating}점 만점 수준"),
            ("3. 빠른 배송", "로켓배송으로 내일 주문하면 바로 사용 가능")
        ]

        y_box = 260
        for title, desc in points:
            draw.rounded_rectangle((80, y_box, 1000, y_box + 160), radius=18, fill="#1E293B", outline="#334155")
            draw.text((120, y_box + 30), title, font=self._get_font(36, bold=True), fill="#FBBF24")
            draw.text((120, y_box + 85), desc, font=self._get_font(30), fill="#CBD5E1")
            y_box += 200

        # Comment Notice Guide
        draw.rounded_rectangle((80, 880, 1000, 1000), radius=20, fill="#E11D48")
        draw.text((130, 922), "▶ 제품 구매처는 [첫 번째 댓글]을 확인하세요!", font=self._get_font(36, bold=True), fill="#FFFFFF")

        file_path = self.output_dir / f"{product_id}_slide2.png"
        img.save(file_path, quality=95)
        return file_path

    def _wrap_text(self, text: str, max_chars_per_line: int) -> str:
        words = text.split()
        lines = []
        current = ""
        for word in words:
            if len(current) + len(word) + 1 <= max_chars_per_line:
                current = f"{current} {word}".strip()
            else:
                if current:
                    lines.append(current)
                current = word
        if current:
            lines.append(current)
        return "\n".join(lines[:2])  # max 2 lines

    def _load_product_image(self, url: Optional[str]) -> Optional[Image.Image]:
        if not url:
            return None
        try:
            res = requests.get(url, timeout=5)
            if res.status_code == 200:
                return Image.open(io.BytesIO(res.content)).convert("RGB")
        except Exception as e:
            save_log("DEBUG", "visual", f"Could not download product image {url}: {e}")
        return None
