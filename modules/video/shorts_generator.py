import os
import asyncio
import subprocess
import requests
import io
from pathlib import Path
from typing import Dict, Any, Optional
from PIL import Image, ImageDraw, ImageFont
import edge_tts
import imageio_ffmpeg

from config.settings import BASE_DIR, load_config
from database.models import Product
from database.db import save_log

VIDEOS_DIR = BASE_DIR / "data" / "videos"
FONT_BOLD = "C:\\Windows\\Fonts\\malgunbd.ttf"
FONT_REGULAR = "C:\\Windows\\Fonts\\malgun.ttf"


class ShortsGenerator:
    """Generates 9:16 vertical 15-second YouTube Shorts video with AI Voiceover and Subtitles."""

    def __init__(self):
        VIDEOS_DIR.mkdir(parents=True, exist_ok=True)
        self.ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
        self.width = 1080
        self.height = 1920

    def _get_font(self, size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
        font_path = FONT_BOLD if bold else FONT_REGULAR
        if os.path.exists(font_path):
            return ImageFont.truetype(font_path, size)
        try:
            return ImageFont.truetype("arial.ttf", size)
        except Exception:
            return ImageFont.load_default()

    def _run_coroutine(self, coro):
        """Runs an async coroutine safely, even if called inside an active event loop."""
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        if loop and loop.is_running():
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                return pool.submit(asyncio.run, coro).result()
        else:
            return asyncio.run(coro)

    async def _generate_voiceover(self, text: str, output_path: str):
        """Generates natural Korean voiceover using Edge TTS neural model."""
        communicate = edge_tts.Communicate(text, "ko-KR-SunHiNeural")
        await communicate.save(output_path)

    def _get_audio_duration(self, audio_path: str) -> float:
        """Probes audio duration using ffmpeg."""
        cmd = [self.ffmpeg_exe, "-i", audio_path]
        res = subprocess.run(cmd, stderr=subprocess.PIPE, stdout=subprocess.PIPE, encoding="utf-8", errors="ignore")
        # Look for "Duration: 00:00:12.34"
        import re
        match = re.search(r"Duration:\s*(\d+):(\d+):(\d+\.\d+)", res.stderr)
        if match:
            hours, minutes, seconds = match.groups()
            return float(hours) * 3600 + float(minutes) * 60 + float(seconds)
        return 12.0  # default fallback duration

    def _render_frames(self, product: Product, item_num: int, hook_text: str) -> tuple[Path, Path]:
        """Renders 2 vertical 1080x1920 frames for the Short."""
        frame1_path = VIDEOS_DIR / f"{product.product_id}_f1.png"
        frame2_path = VIDEOS_DIR / f"{product.product_id}_f2.png"

        # --- FRAME 1: Hook & Problem ---
        img1 = Image.new("RGB", (self.width, self.height), color="#0F172A")
        draw1 = ImageDraw.Draw(img1)

        # Top Tag: Item Number
        tag_text = f"🔥 숏츠 속 #{item_num}번 꿀템"
        draw1.rounded_rectangle((80, 120, 480, 210), radius=16, fill="#E11D48")
        draw1.text((110, 145), tag_text, font=self._get_font(42, bold=True), fill="#FFFFFF")

        # Big Hook Title
        y_pos = 260
        for line in hook_text.split("\n")[:2]:
            draw1.text((80, y_pos), line, font=self._get_font(64, bold=True), fill="#F8FAFC")
            y_pos += 85

        # Product Image (Center)
        prod_img = self._load_product_image(product.image_url)
        center_box = (80, 480, 1000, 1380)
        draw1.rounded_rectangle(center_box, radius=32, fill="#1E293B", outline="#334155", width=3)
        if prod_img:
            prod_img.thumbnail((800, 800), Image.Resampling.LANCZOS)
            px = 80 + (920 - prod_img.width) // 2
            py = 480 + (900 - prod_img.height) // 2
            img1.paste(prod_img, (px, py))

        # Bottom Callout Box
        cta_box = (80, 1440, 1000, 1780)
        draw1.rounded_rectangle(cta_box, radius=24, fill="#1E293B", outline="#2563EB", width=3)
        draw1.text((130, 1480), f"✓ {product.title[:24]}", font=self._get_font(44, bold=True), fill="#FBBF24")
        draw1.text((130, 1560), f"가격: {product.price:,}원 (로켓배송)", font=self._get_font(38), fill="#38BDF8")
        draw1.text((130, 1640), f"평점: ★ {product.rating} ({product.review_count:,}개 리뷰)", font=self._get_font(36), fill="#94A3B8")

        # Bottom Bar
        draw1.rounded_rectangle((80, 1810, 1000, 1890), radius=16, fill="#2563EB")
        draw1.text((150, 1830), f"👉 구매처: 프로필 링크 쇼룸 [#{item_num}번 상품] 클릭!", font=self._get_font(34, bold=True), fill="#FFFFFF")
        img1.save(frame1_path, quality=95)

        # --- FRAME 2: Feature & CTA Detail ---
        img2 = Image.new("RGB", (self.width, self.height), color="#0F172A")
        draw2 = ImageDraw.Draw(img2)

        # Header
        draw2.text((80, 120), f"⚡ #{item_num}번 상품 실사용 포인트", font=self._get_font(44, bold=True), fill="#38BDF8")
        draw2.text((80, 190), "구매 전 꼭 알아둘 장점", font=self._get_font(68, bold=True), fill="#F8FAFC")

        # 3 Points Box
        points = [
            ("1. 가성비 & 품질", f"{product.price:,}원대로 부담 없이 삶의 질 향상"),
            ("2. 검증된 후기", f"실제 리뷰 {product.review_count:,}개 / 평점 {product.rating}점"),
            ("3. 빠른 도착", "로켓배송으로 내일 주문 즉시 바로 수령")
        ]

        yb = 320
        for title, desc in points:
            draw2.rounded_rectangle((80, yb, 1000, yb + 220), radius=24, fill="#1E293B", outline="#334155", width=2)
            draw2.text((130, yb + 40), title, font=self._get_font(48, bold=True), fill="#FBBF24")
            draw2.text((130, yb + 115), desc, font=self._get_font(38), fill="#CBD5E1")
            yb += 260

        # Big CTA Box
        cta_big = (80, 1200, 1000, 1750)
        draw2.rounded_rectangle(cta_big, radius=30, fill="#E11D48")
        draw2.text((150, 1300), f"📌 [#{item_num}번 상품] 구매 방법", font=self._get_font(52, bold=True), fill="#FFFFFF")
        draw2.text((130, 1420), "1. 채널 홈(프로필) 상단 링크 클릭", font=self._get_font(42, bold=True), fill="#F8FAFC")
        draw2.text((130, 1510), f"2. 쇼룸에서 [#{item_num}번] 버튼 누르면 끝!", font=self._get_font(42, bold=True), fill="#FDE047")
        draw2.text((130, 1600), "3. 쿠팡 최저가 & 할인 혜택 바로 이동", font=self._get_font(38), fill="#F8FAFC")

        # Bottom Bar
        draw2.rounded_rectangle((80, 1800, 1000, 1880), radius=16, fill="#2563EB")
        draw2.text((150, 1822), f"👉 구매처: 프로필 링크 쇼룸 [#{item_num}번 상품]", font=self._get_font(34, bold=True), fill="#FFFFFF")
        img2.save(frame2_path, quality=95)

        return frame1_path, frame2_path

    def _load_product_image(self, url: Optional[str]) -> Optional[Image.Image]:
        if not url:
            return None
        try:
            res = requests.get(url, timeout=5)
            if res.status_code == 200:
                return Image.open(io.BytesIO(res.content)).convert("RGB")
        except Exception:
            pass
        return None

    def generate_short(self, product: Product, item_num: int = 1) -> Dict[str, Any]:
        """
        Orchestrates full Shorts generation:
        1. Script -> 2. AI Voiceover (Edge-TTS) -> 3. Pillow Frames -> 4. FFmpeg Video
        """
        save_log("INFO", "shorts", f"Generating 15s Shorts video for #{item_num} {product.title}...")

        # Script
        script_text = (
            f"싱크대 배수구 청소할 때 칫솔 들고 문지르지 마세요. "
            f"{product.title[:15]} 뿌리기만 하면 찌든 물때가 3초 만에 싹 내려갑니다. "
            f"자세한 구매 링크는 채널 프로필 쇼룸 {item_num}번 상품에서 확인하세요!"
        ) if "클리너" in product.title or "청소" in product.title else (
            f"지저분한 충전선 볼 때마다 은근히 신경 쓰이셨죠? "
            f"{product.title[:15]} 붙여놓으면 근처만 가도 착 달라붙어서 1초 만에 정리 끝납니다. "
            f"제품 정보는 채널 프로필 쇼룸 {item_num}번 상품에서 바로 확인하세요!"
        )

        hook_text = "이거 쓰고 살림 피로도\n절반으로 줄었습니다" if "클리너" in product.title else "데스크 정리 끝판왕\n1초 만에 깔끔해집니다"

        # 1. Voiceover
        audio_path = VIDEOS_DIR / f"{product.product_id}_voice.mp3"
        self._run_coroutine(self._generate_voiceover(script_text, str(audio_path)))
        duration = self._get_audio_duration(str(audio_path))
        half_dur = max(3.0, duration / 2.0)

        # 2. Render Frames
        f1_path, f2_path = self._render_frames(product, item_num, hook_text)

        # 3. Stitch Video with FFmpeg
        output_mp4 = VIDEOS_DIR / f"{product.product_id}_shorts.mp4"
        cmd = [
            self.ffmpeg_exe,
            "-loop", "1", "-t", str(half_dur), "-i", str(f1_path),
            "-loop", "1", "-t", str(half_dur + 0.5), "-i", str(f2_path),
            "-i", str(audio_path),
            "-filter_complex", "[0:v][1:v]concat=n=2:v=1:a=0[v]",
            "-map", "[v]", "-map", "2:a",
            "-c:v", "libx264", "-pix_fmt", "yuv420p", "-r", "30",
            "-c:a", "aac", "-shortest",
            "-y", str(output_mp4)
        ]

        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, encoding="utf-8", errors="ignore")
        if res.returncode != 0:
            save_log("ERROR", "shorts", f"FFmpeg video export failed: {res.stderr[:200]}")
            return {"success": False, "error": res.stderr}

        save_log("INFO", "shorts", f"Shorts video exported successfully: {output_mp4.name} ({duration:.1f}s)")

        # YouTube Metadata Pack
        from modules.showroom.builder import ShowroomBuilder
        showroom_url = ShowroomBuilder.get_showroom_url()
        yt_title = f"[#{item_num}] 실제 써보고 놀란 이유! {product.title[:20]} 솔직후기 #shorts"
        yt_desc = (
            f"영상 속 제품 구매처는 채널 프로필 상단 링크 쇼룸 [#{item_num}번 상품]을 클릭하세요!\n"
            f"👉 모바일 쇼룸 주소: {showroom_url}\n\n"
            f"• 상품명: {product.title}\n"
            f"• 가격: {product.price:,}원 (로켓배송)\n\n"
            f"이 포스팅은 쿠팡 파트너스 활동의 일환으로, 이에 따른 일정액의 수수료를 제공받습니다.\n\n"
            f"#쇼츠 #쿠팡 #살림꿀템 #자취템 #내돈내산"
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
            "product": product.title
        }
