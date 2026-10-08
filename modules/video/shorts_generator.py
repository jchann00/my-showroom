import os
import io
import asyncio
import subprocess
import requests
import re
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import imageio_ffmpeg

from config.settings import BASE_DIR, load_config
from database.models import Product
from database.db import save_log
from modules.writer.shorts_script import ShortsScriptWriter
from modules.video.tts_engine import TTSEngine
from modules.visual.product_image_fetcher import ProductImageFetcher

VIDEOS_DIR = BASE_DIR / "data" / "videos"
FONT_BOLD = "C:\\Windows\\Fonts\\malgunbd.ttf"
FONT_REGULAR = "C:\\Windows\\Fonts\\malgun.ttf"


class ShortsGenerator:
    """
    High-Converting 30-Second 9:16 Vertical YouTube Shorts Generator:
    - 5-Scene Dynamic Montage with REAL Product Marketplace Photos & Detail Cuts
    - Empathetic Storytelling Narration Engine (ShortsScriptWriter)
    - Full HD 1080x1920 High-Bitrate H.264 Rendering
    - Dedicated High-Impact Real Product Thumbnail Export
    - Synchronized with Permanent Showroom Numbers
    """

    def __init__(self):
        VIDEOS_DIR.mkdir(parents=True, exist_ok=True)
        self.ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
        self.width = 1080
        self.height = 1920
        self.script_writer = ShortsScriptWriter()
        self.tts = TTSEngine()

    def _get_font(self, size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
        font_path = FONT_BOLD if bold else FONT_REGULAR
        if os.path.exists(font_path):
            try:
                return ImageFont.truetype(font_path, size)
            except Exception:
                pass
        try:
            return ImageFont.truetype("arial.ttf", size)
        except Exception:
            return ImageFont.load_default()

    def _get_audio_duration(self, audio_path: str) -> float:
        """Probes audio duration using ffmpeg."""
        cmd = [self.ffmpeg_exe, "-i", audio_path]
        res = subprocess.run(cmd, stderr=subprocess.PIPE, stdout=subprocess.PIPE, encoding="utf-8", errors="ignore")
        match = re.search(r"Duration:\s*(\d+):(\d+):(\d+\.\d+)", res.stderr)
        if match:
            hours, minutes, seconds = match.groups()
            return float(hours) * 3600 + float(minutes) * 60 + float(seconds)
        return 29.5

    def _create_base_canvas(self) -> Tuple[Image.Image, ImageDraw.Draw]:
        """Creates a modern, cinematic dark studio gradient background."""
        base = Image.new("RGB", (self.width, self.height), color="#090D16")

        # Subtle ambient radial glow in the center
        glow = Image.new("RGBA", (self.width, self.height), (0, 0, 0, 0))
        glow_draw = ImageDraw.Draw(glow)
        glow_draw.ellipse((140, 400, 940, 1200), fill=(30, 58, 138, 45))
        glow = glow.filter(ImageFilter.GaussianBlur(80))
        base.paste(glow, (0, 0), glow)

        draw = ImageDraw.Draw(base)
        return base, draw

    def _load_cut_image(self, cut_path: str) -> Optional[Image.Image]:
        """Loads and returns an image safely."""
        if not cut_path or not os.path.exists(cut_path):
            return None
        try:
            return Image.open(cut_path).convert("RGBA")
        except Exception:
            return None

    def _clean_text(self, text: str) -> str:
        """Removes or replaces emojis with clean Korean typography so standard fonts render without missing glyphs."""
        if not text:
            return ""
        replacements = {
            "🔥": "[HOT]",
            "✨": "[추천]",
            "⚡": "[로켓]",
            "👉": "▶",
            "💡": "[POINT]",
            "📌": "[안내]",
            "👌": "[체크]",
            "⚠️": "[주의]",
            "👇": "▼",
            "💻": "[데스크]",
            "🐾": "[반려동물]",
            "🥗": "[식단]"
        }
        for k, v in replacements.items():
            text = text.replace(k, v)
        # Strip any other 4-byte unicode characters that cause square boxes
        return re.sub(r'[\U00010000-\U0010ffff]', '', text).strip()

    def _draw_product_card(self, canvas: Image.Image, draw: ImageDraw.Draw, img: Optional[Image.Image], box: Tuple[int, int, int, int]):
        """Draws an elevated card with centered, prominently-scaled real product image."""
        x1, y1, x2, y2 = box
        draw.rounded_rectangle((x1, y1, x2, y2), radius=28, fill="#131B2E", outline="#1E293B", width=2)
        if img:
            card_w = x2 - x1 - 50
            card_h = y2 - y1 - 50
            orig_w, orig_h = img.size
            if orig_w > 0 and orig_h > 0:
                scale = min(card_w / orig_w, card_h / orig_h)
                new_w = max(10, int(orig_w * scale))
                new_h = max(10, int(orig_h * scale))
                p_copy = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
                px = x1 + (x2 - x1 - new_w) // 2
                py = y1 + (y2 - y1 - new_h) // 2
                canvas.paste(p_copy, (px, py), p_copy if p_copy.mode == "RGBA" else None)

    # -------------------------------------------------------------
    # 5 Dynamic Storytelling Scenes (matching the 30-sec script)
    # -------------------------------------------------------------

    def _render_scene_1(self, product: Product, item_num: int, script: Dict[str, Any], cut_img: Optional[Image.Image]) -> Path:
        """Scene 1 (0~6s): 오프닝 - 일상 사건 & 공감 후킹."""
        canvas, draw = self._create_base_canvas()
        out_path = VIDEOS_DIR / f"{product.product_id}_sc1.png"

        # Top Badge
        badge_text = self._clean_text(script.get("badge", f"[HOT] 일상 필수 #{item_num}번 꿀템"))
        draw.rounded_rectangle((70, 110, 560, 195), radius=16, fill="#E11D48")
        draw.text((100, 132), badge_text, font=self._get_font(38, bold=True), fill="#FFFFFF")

        # Hook Title
        hook_lines = script.get("hook", "").split("\n")
        y = 230
        for idx, line in enumerate(hook_lines[:2]):
            fill_color = "#FDE047" if idx == 1 else "#F8FAFC"
            draw.text((70, y), self._clean_text(line), font=self._get_font(58, bold=True), fill=fill_color)
            y += 80

        # Center: Real Product Cut 1 (Prominent)
        self._draw_product_card(canvas, draw, cut_img, (70, 440, 1010, 1380))

        # Bottom Feature Pill
        draw.rounded_rectangle((70, 1420, 1010, 1640), radius=20, fill="#1E293B", outline="#334155", width=2)
        draw.text((110, 1460), f"✓ {product.title[:24]}", font=self._get_font(42, bold=True), fill="#F8FAFC")
        draw.text((110, 1540), f"{product.price:,}원  |  [로켓배송]  |  ★ {product.rating}점", font=self._get_font(36, bold=True), fill="#38BDF8")

        # Bottom Navigation CTA
        draw.rounded_rectangle((70, 1680, 1010, 1780), radius=16, fill="#2563EB")
        draw.text((120, 1705), f"▶ 구매처: 프로필 쇼룸 [#{item_num}번] 확인!", font=self._get_font(36, bold=True), fill="#FFFFFF")

        canvas.save(out_path, quality=95)
        return out_path

    def _render_scene_2(self, product: Product, item_num: int, script: Dict[str, Any], cut_img: Optional[Image.Image]) -> Path:
        """Scene 2 (6~12s): 문제 상황 - 없었을 때 겪던 스트레스/위기 공감."""
        canvas, draw = self._create_base_canvas()
        out_path = VIDEOS_DIR / f"{product.product_id}_sc2.png"

        # Problem Header
        draw.text((70, 110), "[주의] 매일 겪던 불편한 순간", font=self._get_font(40, bold=True), fill="#F87171")
        draw.text((70, 175), self._clean_text(script.get("sub_2", "원래는 이것 때문에 스트레스였거든요")), font=self._get_font(54, bold=True), fill="#F8FAFC")

        # Center Product Detail Cut 2
        self._draw_product_card(canvas, draw, cut_img, (70, 280, 1010, 1220))

        # Relatable Stress Cards
        draw.rounded_rectangle((70, 1260, 1010, 1420), radius=20, fill="#1E293B", outline="#EF4444", width=2)
        draw.text((110, 1295), "• 매번 참고 넘기기엔 너무 번거롭던 일상", font=self._get_font(38, bold=True), fill="#FCA5A5")
        draw.text((110, 1355), "시간 낭비에 피로도만 쌓이던 순간들", font=self._get_font(32), fill="#CBD5E1")

        draw.rounded_rectangle((70, 1460, 1010, 1620), radius=20, fill="#1E293B", outline="#334155", width=2)
        draw.text((110, 1495), "• 그날 도착한 택배 하나로 분위기 반전!", font=self._get_font(38, bold=True), fill="#FDE047")
        draw.text((110, 1555), f"직접 써보고 감탄한 {product.title[:16]}", font=self._get_font(32), fill="#38BDF8")

        # Bottom Bar
        draw.rounded_rectangle((70, 1680, 1010, 1780), radius=16, fill="#2563EB")
        draw.text((120, 1705), f"▶ 구매처: 프로필 쇼룸 [#{item_num}번] 확인!", font=self._get_font(36, bold=True), fill="#FFFFFF")

        canvas.save(out_path, quality=95)
        return out_path

    def _render_scene_3(self, product: Product, item_num: int, script: Dict[str, Any], cut_img: Optional[Image.Image]) -> Path:
        """Scene 3 (12~20s): 해결 방법 - 실제 사용 감탄 순간 & 가성비/로켓배송."""
        canvas, draw = self._create_base_canvas()
        out_path = VIDEOS_DIR / f"{product.product_id}_sc3.png"

        # Header
        draw.text((70, 110), f"★ #{item_num}번 실제 써보고 감탄한 이유", font=self._get_font(40, bold=True), fill="#38BDF8")
        draw.text((70, 175), f"{product.price:,}원대로 삶의 질 즉시 해결", font=self._get_font(56, bold=True), fill="#F8FAFC")

        # Center Product In-Use Cut 3
        self._draw_product_card(canvas, draw, cut_img, (70, 270, 1010, 1180))

        # Real Value Box
        draw.rounded_rectangle((70, 1220, 1010, 1420), radius=22, fill="#131B2E", outline="#2563EB", width=2)
        draw.text((110, 1255), f"판매가: {product.price:,}원", font=self._get_font(52, bold=True), fill="#FBBF24")
        draw.rounded_rectangle((620, 1255, 830, 1315), radius=10, fill="#14532D")
        draw.text((645, 1270), "로켓배송", font=self._get_font(30, bold=True), fill="#4ADE80")
        draw.text((110, 1345), f"실제 사용자 평점 ★ {product.rating}점 ({product.review_count:,}개 리뷰)", font=self._get_font(34), fill="#94A3B8")

        # Solution Highlight
        draw.rounded_rectangle((70, 1460, 1010, 1620), radius=20, fill="#1E293B", outline="#38BDF8", width=2)
        draw.text((110, 1495), f"[POINT] {self._clean_text(script.get('sub_3', '말끔하게 고민 해결 완료!'))}", font=self._get_font(38, bold=True), fill="#38BDF8")
        draw.text((110, 1555), "힘들게 고민할 필요 없이 한번 쓰면 정착하게 됩니다", font=self._get_font(32), fill="#CBD5E1")

        # Bottom Bar
        draw.rounded_rectangle((70, 1680, 1010, 1780), radius=16, fill="#2563EB")
        draw.text((120, 1705), f"▶ 구매처: 프로필 쇼룸 [#{item_num}번] 확인!", font=self._get_font(36, bold=True), fill="#FFFFFF")

        canvas.save(out_path, quality=95)
        return out_path

    def _render_scene_4(self, product: Product, item_num: int, script: Dict[str, Any], cut_img: Optional[Image.Image]) -> Path:
        """Scene 4 (20~25s): 활용 디테일 - 누구나 쉽게 쓰는 편의성 & 품질 만족도."""
        canvas, draw = self._create_base_canvas()
        out_path = VIDEOS_DIR / f"{product.product_id}_sc4.png"

        # Header
        draw.text((70, 110), "[CHECK] 초보자도 부담 없이 간편 사용", font=self._get_font(40, bold=True), fill="#4ADE80")
        draw.text((70, 175), self._clean_text(script.get("sub_4", "누구나 쉽게 쓸 수 있는 실용템")), font=self._get_font(54, bold=True), fill="#F8FAFC")

        # Center Product Detail Cut 4
        self._draw_product_card(canvas, draw, cut_img, (70, 270, 1010, 1180))

        # Checkpoints
        points = [
            ("검증된 품질", f"평점 {product.rating}점 / 리뷰 {product.review_count:,}개 입증"),
            ("부담 없는 사용", "복잡한 사용법 없이 바로 꺼내서 활용 가능"),
            ("내일 바로 수령", "로켓배송으로 빠르게 받아보는 혜택")
        ]
        y_pos = 1220
        for title, desc in points:
            draw.rounded_rectangle((70, y_pos, 1010, y_pos + 120), radius=16, fill="#1E293B", outline="#334155", width=2)
            draw.text((110, y_pos + 22), f"✓ {title}:", font=self._get_font(34, bold=True), fill="#FDE047")
            draw.text((360, y_pos + 24), desc, font=self._get_font(32), fill="#F8FAFC")
            y_pos += 140

        # Bottom Bar
        draw.rounded_rectangle((70, 1680, 1010, 1780), radius=16, fill="#2563EB")
        draw.text((120, 1705), f"▶ 구매처: 프로필 쇼룸 [#{item_num}번] 확인!", font=self._get_font(36, bold=True), fill="#FFFFFF")

        canvas.save(out_path, quality=95)
        return out_path

    def _render_scene_5(self, product: Product, item_num: int, script: Dict[str, Any], cut_img: Optional[Image.Image]) -> Path:
        """Scene 5 (25~30s): 마무리 멘트 & 쇼룸 행동 유도 CTA."""
        canvas, draw = self._create_base_canvas()
        out_path = VIDEOS_DIR / f"{product.product_id}_sc5.png"

        # Big Vibrant CTA Container
        cta_box = (70, 160, 1010, 1420)
        draw.rounded_rectangle(cta_box, radius=32, fill="#E11D48")

        draw.text((120, 220), "[안내] 구매 링크는 어디에 있나요?", font=self._get_font(54, bold=True), fill="#FFFFFF")

        # Step 1
        draw.rounded_rectangle((110, 320, 970, 520), radius=20, fill="#991B1B")
        draw.text((150, 360), "1단계: 채널 프로필(홈) 링크 클릭", font=self._get_font(42, bold=True), fill="#F8FAFC")
        draw.text((150, 430), "유튜브 프로필 링크 누르면 쇼룸 웹페이지 연결!", font=self._get_font(30), fill="#FDE047")

        # Step 2
        draw.rounded_rectangle((110, 560, 970, 780), radius=20, fill="#991B1B")
        draw.text((150, 600), f"2단계: 쇼룸에서 [#{item_num}번 상품] 바로 클릭", font=self._get_font(42, bold=True), fill="#FDE047")
        draw.text((150, 680), "영상 번호와 동일한 번호 누르면 1초 만에 연결!", font=self._get_font(30), fill="#F8FAFC")

        # Mini Product Preview in Step 3
        draw.rounded_rectangle((110, 820, 970, 1040), radius=20, fill="#991B1B")
        draw.text((150, 860), f"3단계: 쿠팡 {product.price:,}원 최저가 확인", font=self._get_font(42, bold=True), fill="#F8FAFC")
        draw.text((150, 930), "로켓배송으로 내일 바로 도착!", font=self._get_font(30), fill="#FDE047")

        # Product Card
        self._draw_product_card(canvas, draw, cut_img, (110, 1070, 970, 1380))

        # Action Arrow
        draw.text((180, 1480), "▼ 지금 바로 채널 프로필 링크 클릭! ▼", font=self._get_font(46, bold=True), fill="#38BDF8")

        # Giant Bottom Button
        draw.rounded_rectangle((70, 1580, 1010, 1760), radius=24, fill="#2563EB")
        draw.text((140, 1630), f"▶ 프로필 쇼룸 [#{item_num}번] 바로가기", font=self._get_font(48, bold=True), fill="#FFFFFF")

        canvas.save(out_path, quality=95)
        return out_path

    # -------------------------------------------------------------
    # Dedicated High-Impact Real Product Thumbnail
    # -------------------------------------------------------------

    def _render_thumbnail(self, product: Product, item_num: int, hero_img: Optional[Image.Image]) -> Path:
        """Renders an eye-catching 1080x1920 YouTube Shorts Thumbnail featuring the REAL product."""
        canvas, draw = self._create_base_canvas()
        out_path = VIDEOS_DIR / f"{product.product_id}_thumbnail.jpg"

        # Top Badge
        draw.rounded_rectangle((70, 120, 600, 210), radius=18, fill="#E11D48")
        draw.text((100, 142), f"[BEST] 쇼츠 속 #{item_num}번 필수 꿀템", font=self._get_font(40, bold=True), fill="#FFFFFF")

        # Headline
        draw.text((70, 250), "이건 진짜 필요하겠다 싶어", font=self._get_font(56, bold=True), fill="#F8FAFC")
        draw.text((70, 330), "직접 써본 실사용 솔직후기", font=self._get_font(64, bold=True), fill="#FDE047")

        # Center: Large Real Product Showcase (Prominent & High-Impact)
        self._draw_product_card(canvas, draw, hero_img, (70, 440, 1010, 1400))

        # Bottom Price & Trust Badges
        draw.rounded_rectangle((70, 1440, 1010, 1640), radius=22, fill="#131B2E", outline="#2563EB", width=2)
        draw.text((110, 1480), f"{product.title[:24]}", font=self._get_font(42, bold=True), fill="#F8FAFC")
        draw.text((110, 1555), f"{product.price:,}원  |  [로켓배송]  |  ★ {product.rating}점", font=self._get_font(38, bold=True), fill="#38BDF8")

        # Bottom CTA Banner
        draw.rounded_rectangle((70, 1680, 1010, 1780), radius=16, fill="#2563EB")
        draw.text((140, 1705), f"▶ 프로필 링크 쇼룸 [#{item_num}번] 확인!", font=self._get_font(40, bold=True), fill="#FFFFFF")

        canvas.save(out_path, quality=95)
        return out_path

    # -------------------------------------------------------------
    # Full Generation Pipeline
    # -------------------------------------------------------------

    def generate_short(self, product: Product, item_num: int = 1) -> Dict[str, Any]:
        """
        Orchestrates full 30-Second High-Quality Shorts generation:
        1. 30s Empathetic Storytelling Script (5 stages)
        2. Natural Voiceover (TTS/Voice Cloning) calibrated for ~28-32s
        3. Real Product Detail Cuts fetched from marketplace CDN
        4. 5 Dynamic Visual Scenes + High-Impact Real Thumbnail
        5. FFmpeg High-Bitrate Concat & Neon Animated Progress Bar
        """
        save_log("INFO", "shorts", f"Generating 30-sec Storytelling Shorts for #{item_num} {product.title}...")

        # 1. 30s Persuasive Storytelling Script
        script_pkg = self.script_writer.generate_script(product, item_num)
        narration_text = script_pkg["narration"]

        # 2. Voiceover (Voice Cloning or High-Quality Edge Neural Voice)
        audio_path = VIDEOS_DIR / f"{product.product_id}_voice.mp3"
        self.tts.generate_audio(narration_text, str(audio_path))
        duration = self._get_audio_duration(str(audio_path))
        duration = max(26.0, duration)  # Ensure at least 26~30s

        # 3. Fetch REAL Marketplace Product Images & Multiple Detail Cuts
        cuts = ProductImageFetcher.fetch_product_images(product.product_id, product.title, product.category)
        loaded_cuts = [self._load_cut_image(p) for p in cuts if os.path.exists(p)]
        while len(loaded_cuts) < 4:
            loaded_cuts.append(loaded_cuts[0] if loaded_cuts else None)

        # 4. Render 5 Distinct Scenes
        sc1_path = self._render_scene_1(product, item_num, script_pkg, loaded_cuts[0])
        sc2_path = self._render_scene_2(product, item_num, script_pkg, loaded_cuts[1] or loaded_cuts[0])
        sc3_path = self._render_scene_3(product, item_num, script_pkg, loaded_cuts[2] or loaded_cuts[0])
        sc4_path = self._render_scene_4(product, item_num, script_pkg, loaded_cuts[3] or loaded_cuts[0])
        sc5_path = self._render_scene_5(product, item_num, script_pkg, loaded_cuts[0])

        # 5. Render Dedicated Real Product Thumbnail
        thumb_path = self._render_thumbnail(product, item_num, loaded_cuts[0])

        # Scene Durations across ~30 seconds (Opening 20%, Problem 20%, Solution 25%, Detail 15%, CTA 20%)
        d1 = round(duration * 0.20, 2)
        d2 = round(duration * 0.20, 2)
        d3 = round(duration * 0.25, 2)
        d4 = round(duration * 0.15, 2)
        d5 = round(duration - d1 - d2 - d3 - d4 + 0.5, 2)

        # 6. Stitch with High-Bitrate H.264 & Animated Red Progress Bar
        output_mp4 = VIDEOS_DIR / f"{product.product_id}_shorts.mp4"

        # Concat 5 scenes + animated bottom progress bar
        filter_str = (
            f"[0:v][1:v][2:v][3:v][4:v]concat=n=5:v=1:a=0[vcat];"
            f"[vcat]drawbox=x=0:y=1904:w=iw*t/{duration:.2f}:h=16:color=#E11D48:t=fill[vout]"
        )

        cmd = [
            self.ffmpeg_exe,
            "-loop", "1", "-t", str(d1), "-i", str(sc1_path),
            "-loop", "1", "-t", str(d2), "-i", str(sc2_path),
            "-loop", "1", "-t", str(d3), "-i", str(sc3_path),
            "-loop", "1", "-t", str(d4), "-i", str(sc4_path),
            "-loop", "1", "-t", str(d5), "-i", str(sc5_path),
            "-i", str(audio_path),
            "-filter_complex", filter_str,
            "-map", "[vout]", "-map", "5:a",
            "-c:v", "libx264", "-crf", "18", "-preset", "fast",
            "-pix_fmt", "yuv420p", "-r", "30",
            "-c:a", "aac", "-b:a", "192k", "-shortest",
            "-y", str(output_mp4)
        ]

        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, encoding="utf-8", errors="ignore")
        if res.returncode != 0:
            save_log("ERROR", "shorts", f"FFmpeg video export failed: {res.stderr[:200]}")
            return {"success": False, "error": res.stderr}

        save_log("INFO", "shorts", f"30-Sec Storytelling Shorts exported: {output_mp4.name} ({duration:.1f}s)")

        # YouTube Metadata
        from modules.showroom.builder import ShowroomBuilder
        showroom_url = ShowroomBuilder.get_showroom_url()
        titles = script_pkg.get("titles", [])
        yt_title = titles[0] if titles else f"[#{item_num}] {product.title[:20]} 솔직후기 #shorts"

        yt_desc = (
            f"{script_pkg.get('narration')}\n\n"
            f"📌 구매 링크: 채널 프로필 쇼룸 [#{item_num}번 상품] 확인!\n"
            f"• 제품 번호: #{item_num}번\n"
            f"• 가격: {product.price:,}원 (로켓배송)\n\n"
            f"이 포스팅은 쿠팡 파트너스 활동의 일환으로, 이에 따른 일정액의 수수료를 제공받습니다.\n\n"
            f"#쇼츠 #쿠팡 #살림꿀템 #자취템 #내돈내산 #{product.category}"
        )
        tags = ["쇼츠", "쿠팡", "살림꿀템", "자취템", "내돈내산", product.category]

        return {
            "success": True,
            "video_path": str(output_mp4),
            "video_filename": output_mp4.name,
            "thumbnail_path": str(thumb_path),
            "duration": duration,
            "title": yt_title,
            "titles": titles,
            "description": yt_desc,
            "tags": tags,
            "item_number": item_num,
            "product": product.title,
            "script": script_pkg
        }
