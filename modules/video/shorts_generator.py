import os
import asyncio
import subprocess
import requests
import io
import re
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import imageio_ffmpeg

from config.settings import BASE_DIR, load_config
from database.models import Product
from database.db import save_log
from modules.writer.shorts_script import ShortsScriptWriter
from modules.video.tts_engine import TTSEngine

VIDEOS_DIR = BASE_DIR / "data" / "videos"
FONT_BOLD = "C:\\Windows\\Fonts\\malgunbd.ttf"
FONT_REGULAR = "C:\\Windows\\Fonts\\malgun.ttf"


class ShortsGenerator:
    """
    High-Quality 9:16 Vertical YouTube Shorts Generator with:
    - Product-tailored AI Viral Scripts (ShortsScriptWriter)
    - Natural Korean Voiceover & Voice Cloning Support (TTSEngine)
    - 3-Scene Dynamic Visual Montage & Animated Bottom Progress Bar
    - Full HD 1080x1920 High-Bitrate H.264 Rendering
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
        return 13.5

    def _create_base_canvas(self) -> Tuple[Image.Image, ImageDraw.Draw]:
        """Creates a modern, cinematic dark studio gradient background."""
        base = Image.new("RGB", (self.width, self.height), color="#090D16")
        draw = ImageDraw.Draw(base)

        # Subtle ambient radial glow in the center
        glow = Image.new("RGBA", (self.width, self.height), (0, 0, 0, 0))
        glow_draw = ImageDraw.Draw(glow)
        glow_draw.ellipse((140, 400, 940, 1200), fill=(30, 58, 138, 45))  # Deep indigo glow
        glow = glow.filter(ImageFilter.GaussianBlur(80))
        base.paste(glow, (0, 0), glow)

        return base, draw

    def _load_product_image(self, url: Optional[str]) -> Optional[Image.Image]:
        if not url:
            return None
        try:
            res = requests.get(url, timeout=5)
            if res.status_code == 200:
                return Image.open(io.BytesIO(res.content)).convert("RGBA")
        except Exception:
            pass
        return None

    def _render_scene_1(self, product: Product, item_num: int, script_pkg: Dict[str, Any], prod_img: Optional[Image.Image]) -> Path:
        """Scene 1: 0~4s Hook & Curiosity Trigger."""
        canvas, draw = self._create_base_canvas()
        out_path = VIDEOS_DIR / f"{product.product_id}_sc1.png"

        # Top Tag: Category & Badge
        badge_text = script_pkg.get("badge", f"🔥 숏츠 속 #{item_num}번 꿀템")
        draw.rounded_rectangle((70, 110, 540, 195), radius=16, fill="#E11D48")
        draw.text((100, 132), badge_text, font=self._get_font(38, bold=True), fill="#FFFFFF")

        # Big Hook Title (High-contrast yellow & white)
        hook_lines = script_pkg.get("hook", "").split("\n")
        y = 230
        for idx, line in enumerate(hook_lines[:2]):
            fill_color = "#FDE047" if idx == 1 else "#F8FAFC"
            draw.text((70, y), line, font=self._get_font(60, bold=True), fill=fill_color)
            y += 82

        # Center: Product Showcase Card
        card_box = (70, 440, 1010, 1380)
        draw.rounded_rectangle(card_box, radius=28, fill="#131B2E", outline="#1E293B", width=2)
        if prod_img:
            p_copy = prod_img.copy()
            p_copy.thumbnail((780, 780), Image.Resampling.LANCZOS)
            px = 70 + (940 - p_copy.width) // 2
            py = 440 + (940 - p_copy.height) // 2
            canvas.paste(p_copy, (px, py), p_copy if p_copy.mode == "RGBA" else None)

        # Bottom Feature Pill
        draw.rounded_rectangle((70, 1420, 1010, 1640), radius=20, fill="#1E293B", outline="#334155", width=2)
        draw.text((110, 1460), f"✓ {product.title[:24]}", font=self._get_font(42, bold=True), fill="#F8FAFC")
        draw.text((110, 1540), f"{product.price:,}원  |  ⚡ 로켓배송  |  ★ {product.rating}점", font=self._get_font(36, bold=True), fill="#38BDF8")

        # Bottom CTA Banner
        draw.rounded_rectangle((70, 1680, 1010, 1780), radius=16, fill="#2563EB")
        draw.text((120, 1705), f"👉 구매처: 프로필 링크 쇼룸 [#{item_num}번] 확인!", font=self._get_font(36, bold=True), fill="#FFFFFF")

        canvas.save(out_path, quality=95)
        return out_path

    def _render_scene_2(self, product: Product, item_num: int, script_pkg: Dict[str, Any], prod_img: Optional[Image.Image]) -> Path:
        """Scene 2: 4~10s Real Value, Price & Social Proof."""
        canvas, draw = self._create_base_canvas()
        out_path = VIDEOS_DIR / f"{product.product_id}_sc2.png"

        # Top Header
        draw.text((70, 110), f"⚡ #{item_num}번 상품 실사용 포인트", font=self._get_font(40, bold=True), fill="#38BDF8")
        draw.text((70, 175), "실제 써보고 놀란 이유", font=self._get_font(62, bold=True), fill="#F8FAFC")

        # Upper Product Mini Preview with Big Price
        draw.rounded_rectangle((70, 280, 1010, 620), radius=24, fill="#131B2E", outline="#2563EB", width=2)
        if prod_img:
            p_mini = prod_img.copy()
            p_mini.thumbnail((300, 300), Image.Resampling.LANCZOS)
            canvas.paste(p_mini, (100, 300), p_mini if p_mini.mode == "RGBA" else None)

        draw.text((430, 340), f"{product.price:,}원", font=self._get_font(64, bold=True), fill="#FBBF24")
        draw.rounded_rectangle((430, 440, 620, 495), radius=10, fill="#14532D")
        draw.text((450, 452), "⚡ 로켓배송", font=self._get_font(28, bold=True), fill="#4ADE80")
        draw.text((430, 525), f"평점 ★ {product.rating} ({product.review_count:,}개 리뷰)", font=self._get_font(32), fill="#94A3B8")

        # 3 Key Value Cards
        points = [
            ("가성비 & 부담 제로", f"{product.price:,}원대로 삶의 질 즉시 업그레이드"),
            ("실사용 압도적 호평", f"누적 리뷰 {product.review_count:,}개 검증 완료"),
            ("빠른 수령", "로켓배송으로 주문 시 내일 바로 도착")
        ]
        y_pos = 660
        for title, desc in points:
            draw.rounded_rectangle((70, y_pos, 1010, y_pos + 180), radius=20, fill="#1E293B", outline="#334155", width=2)
            draw.text((110, y_pos + 30), f"• {title}", font=self._get_font(42, bold=True), fill="#FDE047")
            draw.text((110, y_pos + 95), desc, font=self._get_font(34), fill="#CBD5E1")
            y_pos += 210

        # Subtitle Callout
        sub_text = script_pkg.get("sub_2", f"{product.title[:20]}")
        draw.rounded_rectangle((70, 1340, 1010, 1460), radius=18, fill="#0F172A", outline="#38BDF8", width=2)
        draw.text((110, 1375), f"💡 {sub_text}", font=self._get_font(38, bold=True), fill="#38BDF8")

        # Bottom Bar
        draw.rounded_rectangle((70, 1680, 1010, 1780), radius=16, fill="#2563EB")
        draw.text((120, 1705), f"👉 구매처: 프로필 링크 쇼룸 [#{item_num}번] 확인!", font=self._get_font(36, bold=True), fill="#FFFFFF")

        canvas.save(out_path, quality=95)
        return out_path

    def _render_scene_3(self, product: Product, item_num: int, script_pkg: Dict[str, Any]) -> Path:
        """Scene 3: 10~15s Action CTA & Showroom Navigation."""
        canvas, draw = self._create_base_canvas()
        out_path = VIDEOS_DIR / f"{product.product_id}_sc3.png"

        # Big Vibrant CTA Container
        cta_box = (70, 240, 1010, 1280)
        draw.rounded_rectangle(cta_box, radius=32, fill="#E11D48")

        draw.text((120, 320), "📌 구매 링크는 어디에 있나요?", font=self._get_font(52, bold=True), fill="#FFFFFF")

        # Step 1
        draw.rounded_rectangle((110, 440, 970, 640), radius=20, fill="#991B1B")
        draw.text((150, 480), "1단계: 채널 홈(프로필) 상단 링크 클릭", font=self._get_font(40, bold=True), fill="#F8FAFC")
        draw.text((150, 550), "유튜브 프로필 링크 누르면 쇼룸 웹페이지 연결!", font=self._get_font(30), fill="#FDE047")

        # Step 2
        draw.rounded_rectangle((110, 680, 970, 880), radius=20, fill="#991B1B")
        draw.text((150, 720), f"2단계: 쇼룸에서 [#{item_num}번 상품] 버튼 클릭", font=self._get_font(40, bold=True), fill="#FDE047")
        draw.text((150, 790), "영상 번호와 동일한 번호 누르면 1초 만에 끝!", font=self._get_font(30), fill="#F8FAFC")

        # Step 3
        draw.rounded_rectangle((110, 920, 970, 1120), radius=20, fill="#991B1B")
        draw.text((150, 960), "3단계: 쿠팡 최저가 & 로켓배송 바로 이동", font=self._get_font(40, bold=True), fill="#F8FAFC")
        draw.text((150, 1030), f"{product.price:,}원 최저가 혜택 바로 확인 가능", font=self._get_font(30), fill="#FDE047")

        # Arrow Guide
        draw.text((220, 1380), "👇 지금 바로 프로필 링크 클릭! 👇", font=self._get_font(46, bold=True), fill="#38BDF8")

        # Giant Bottom Button
        draw.rounded_rectangle((70, 1520, 1010, 1680), radius=24, fill="#2563EB")
        draw.text((160, 1570), f"👉 프로필 쇼룸 [#{item_num}번] 바로가기", font=self._get_font(46, bold=True), fill="#FFFFFF")

        canvas.save(out_path, quality=95)
        return out_path

    def generate_short(self, product: Product, item_num: int = 1) -> Dict[str, Any]:
        """
        Orchestrates full High-Quality Shorts generation:
        1. Custom AI Script -> 2. Voiceover (TTS/Voice Cloning) -> 3. 3-Scene Visuals -> 4. FFmpeg Video
        """
        save_log("INFO", "shorts", f"Generating dynamic High-Quality Shorts for #{item_num} {product.title}...")

        # 1. Custom Script
        script_pkg = self.script_writer.generate_script(product, item_num)
        narration_text = script_pkg["narration"]

        # 2. Voiceover (Voice Cloning or High-Quality Edge Neural Voice)
        audio_path = VIDEOS_DIR / f"{product.product_id}_voice.mp3"
        self.tts.generate_audio(narration_text, str(audio_path))
        duration = self._get_audio_duration(str(audio_path))
        duration = max(11.0, duration)

        # 3. Dynamic 3-Scene Visual Frames
        prod_img = self._load_product_image(product.image_url)
        sc1_path = self._render_scene_1(product, item_num, script_pkg, prod_img)
        sc2_path = self._render_scene_2(product, item_num, script_pkg, prod_img)
        sc3_path = self._render_scene_3(product, item_num, script_pkg)

        # Scene Durations (30% hook, 40% proof, 30% cta)
        d1 = round(duration * 0.30, 2)
        d2 = round(duration * 0.40, 2)
        d3 = round(duration - d1 - d2 + 0.5, 2)

        # 4. Stitch with High-Bitrate H.264 & Animated Red Progress Bar
        output_mp4 = VIDEOS_DIR / f"{product.product_id}_shorts.mp4"

        # FFmpeg filter: concat 3 scenes + animated bottom progress bar
        filter_str = (
            f"[0:v][1:v][2:v]concat=n=3:v=1:a=0[vcat];"
            f"[vcat]drawbox=x=0:y=1904:w=iw*t/{duration:.2f}:h=16:color=#E11D48:t=fill[vout]"
        )

        cmd = [
            self.ffmpeg_exe,
            "-loop", "1", "-t", str(d1), "-i", str(sc1_path),
            "-loop", "1", "-t", str(d2), "-i", str(sc2_path),
            "-loop", "1", "-t", str(d3), "-i", str(sc3_path),
            "-i", str(audio_path),
            "-filter_complex", filter_str,
            "-map", "[vout]", "-map", "3:a",
            "-c:v", "libx264", "-crf", "18", "-preset", "fast",
            "-pix_fmt", "yuv420p", "-r", "30",
            "-c:a", "aac", "-b:a", "192k", "-shortest",
            "-y", str(output_mp4)
        ]

        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, encoding="utf-8", errors="ignore")
        if res.returncode != 0:
            save_log("ERROR", "shorts", f"FFmpeg video export failed: {res.stderr[:200]}")
            return {"success": False, "error": res.stderr}

        save_log("INFO", "shorts", f"High-Quality Shorts video exported: {output_mp4.name} ({duration:.1f}s)")

        # YouTube Metadata
        from modules.showroom.builder import ShowroomBuilder
        showroom_url = ShowroomBuilder.get_showroom_url()
        yt_title = f"[#{item_num}] {script_pkg.get('sub_1', product.title[:15])}! {product.title[:18]} 솔직후기 #shorts"
        yt_desc = (
            f"{script_pkg.get('narration')}\n\n"
            f"👉 모바일 쇼룸 주소: {showroom_url}\n"
            f"• 제품 번호: #{item_num}번 상품\n"
            f"• 가격: {product.price:,}원 (로켓배송)\n\n"
            f"이 포스팅은 쿠팡 파트너스 활동의 일환으로, 이에 따른 일정액의 수수료를 제공받습니다.\n\n"
            f"#쇼츠 #쿠팡 #살림꿀템 #자취템 #내돈내산 #{product.category}"
        )
        tags = ["쇼츠", "쿠팡", "살림꿀템", "자취템", "내돈내산", product.category]

        return {
            "success": True,
            "video_path": str(output_mp4),
            "video_filename": output_mp4.name,
            "duration": duration,
            "title": yt_title,
            "description": yt_desc,
            "tags": tags,
            "item_number": item_num,
            "product": product.title,
            "script": script_pkg
        }
