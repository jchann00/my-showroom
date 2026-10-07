import time
import json
import random
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from config.settings import load_config
from database.models import Product, PostRecord
from database.db import (
    save_product, get_pending_product, mark_product_posted,
    save_post_record, save_log, get_stats
)
from modules.sourcing.coupang_crawler import CoupangCrawler
from modules.sourcing.coupang_api import CoupangApiClient
from modules.deeplink.link_manager import DeepLinkManager
from modules.writer.generator import PostGenerator
from modules.visual.card_generator import CardGenerator
from modules.publisher.threads_api import ThreadsPublisher
from modules.publisher.instagram_api import InstagramPublisher
from modules.publisher.notify import NotificationManager


class AutoPilotScheduler:
    """End-to-end autonomous scheduler for hands-off monetization & posting."""

    def __init__(self):
        self.scheduler = BackgroundScheduler()
        self.crawler = CoupangCrawler()
        self.coupang_api = CoupangApiClient()
        self.link_manager = DeepLinkManager()
        self.generator = PostGenerator()
        self.visual = CardGenerator()
        self.threads = ThreadsPublisher()
        self.instagram = InstagramPublisher()
        self.notify = NotificationManager()
        self.is_running = False

    def start(self):
        """Schedule golden time posting jobs and start background engine."""
        if self.is_running:
            return

        cfg = load_config()
        golden_hours = cfg.get("strategy", {}).get("golden_hours", ["07:30", "12:30", "21:30"])

        self.scheduler.remove_all_jobs()
        for gh in golden_hours:
            try:
                hour, minute = gh.split(":")
                self.scheduler.add_job(
                    self.execute_scheduled_post,
                    trigger=CronTrigger(hour=int(hour), minute=int(minute)),
                    id=f"job_{hour}_{minute}",
                    name=f"Golden Time {gh} Post",
                    replace_existing=True
                )
                save_log("INFO", "scheduler", f"Scheduled golden-time job registered at {gh}")
            except Exception as e:
                save_log("ERROR", "scheduler", f"Failed to register cron for {gh}: {e}")

        self.scheduler.start()
        self.is_running = True
        save_log("INFO", "scheduler", "Auto-Pilot Scheduler successfully started in background.")

    def stop(self):
        """Stop background scheduler."""
        if self.is_running:
            self.scheduler.shutdown(wait=False)
            self.is_running = False
            save_log("INFO", "scheduler", "Auto-Pilot Scheduler stopped.")

    def execute_scheduled_post(self):
        """Entry point for scheduled jobs with anti-bot jitter."""
        cfg = load_config()
        jitter_minutes = cfg.get("strategy", {}).get("jitter_minutes", 10)
        if jitter_minutes > 0:
            delay = random.randint(0, jitter_minutes * 60)
            save_log("INFO", "scheduler", f"Anti-bot jitter: sleeping {delay // 60}m {delay % 60}s before posting...")
            time.sleep(delay)

        modules = cfg.get("modules", {})
        if modules.get("shorts_enabled", True):
            self.trigger_shorts_cycle()
        if modules.get("threads_enabled", False):
            self.trigger_one_post()

    def trigger_shorts_cycle(self) -> Dict[str, Any]:
        """
        Executes a complete 15-second Shorts generation cycle:
        1. Sources product from Coupang
        2. Converts tracking deep link
        3. Generates 9:16 vertical video with AI voiceover (Edge-TTS) & subtitles
        4. Automatically updates mobile Showroom web catalog with item #1
        """
        save_log("INFO", "shorts", "Starting autonomous Shorts & Showroom cycle...")
        product = get_pending_product()
        if not product:
            self.crawler.fetch_and_store_candidates()
            product = get_pending_product()

        if not product:
            save_log("WARNING", "shorts", "No products available for Shorts.")
            return {"success": False, "error": "No product available"}

        # 1. Deeplink
        deeplink = self.link_manager.ensure_deeplink(product)

        # 2. Sequential Item Number
        stats = get_stats()
        item_num = (stats.get("total_products", 1))

        # 3. Generate 15-sec Vertical Shorts MP4
        from modules.video.shorts_generator import ShortsGenerator
        generator = ShortsGenerator()
        short_res = generator.generate_short(product, item_num=item_num)

        # 4. Auto-update Showroom HTML
        from modules.showroom.builder import ShowroomBuilder
        ShowroomBuilder.build_showroom_html()
        save_log("INFO", "showroom", f"Showroom catalog updated with #{item_num} {product.title}")

        # Mark posted
        mark_product_posted(product.product_id)

        # Record post
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        post_record = PostRecord(
            product_id=product.product_id,
            post_type="shorts",
            platform="youtube",
            main_text=short_res.get("title", ""),
            comment_1=short_res.get("description", ""),
            image_paths=short_res.get("video_path", ""),
            status="rendered",
            published_at=now_str
        )
        post_id = save_post_record(post_record)

        # Webhook Alert
        self.notify.send_post_alert(
            title=f"[쇼츠 #{item_num}] {product.title}",
            category=product.category,
            price=product.price,
            deeplink=deeplink,
            status="Shorts Rendered + Showroom Updated"
        )

        return {
            "success": True,
            "post_type": "shorts",
            "post_id": post_id,
            "item_num": item_num,
            "product": product.title,
            "video_path": short_res.get("video_path"),
            "video_filename": short_res.get("video_filename"),
            "title": short_res.get("title"),
            "description": short_res.get("description"),
            "tags": short_res.get("tags")
        }

    def trigger_one_post(self, force_affiliate: bool = False) -> Dict[str, Any]:
        """Executes a single Threads posting cycle."""
        save_log("INFO", "pipeline", "Starting autonomous posting cycle...")
        cfg = load_config()
        strategy = cfg.get("strategy", {})
        affiliate_ratio = strategy.get("affiliate_ratio", 1)
        info_ratio = strategy.get("info_post_ratio", 3)

        # Check content ratio in recent posts
        stats = get_stats()
        recent_types = stats.get("recent_post_types", [])

        # Determine if this post should be affiliate or info
        is_affiliate = force_affiliate
        if not force_affiliate:
            recent_affiliate_count = recent_types[:info_ratio].count("affiliate")
            if recent_affiliate_count >= affiliate_ratio:
                is_affiliate = False
            else:
                is_affiliate = True

        if is_affiliate:
            return self._run_affiliate_cycle()
        else:
            return self._run_info_cycle()

    def _run_affiliate_cycle(self) -> Dict[str, Any]:
        """Runs full affiliate monetization cycle."""
        # 1. Source Product
        product = get_pending_product()
        if not product:
            save_log("INFO", "pipeline", "No pending products in DB. Running crawler to source candidates...")
            self.crawler.fetch_and_store_candidates()
            product = get_pending_product()

        if not product:
            save_log("WARNING", "pipeline", "No suitable products found even after sourcing. Falling back to info post.")
            return self._run_info_cycle()

        save_log("INFO", "pipeline", f"Selected product: [{product.category}] {product.title}")

        # 2. Link Conversion
        deeplink = self.link_manager.ensure_deeplink(product)

        # 3. Copywriting (LLM)
        copy_pkg = self.generator.generate_affiliate_post(product, deeplink)

        # 4. Visual Card Generation
        card_paths = self.visual.generate_cards(
            product_id=product.product_id,
            headline=copy_pkg["card_headline"],
            subtext=copy_pkg["card_subtext"],
            category=product.category,
            price=product.price,
            rating=product.rating,
            review_count=product.review_count,
            image_url=product.image_url
        )

        # Upload slide 1 to public CDN for Meta Graph API if available
        from modules.visual.uploader import ImageUploader
        public_image_url = None
        if card_paths and len(card_paths) > 0:
            public_image_url = ImageUploader.upload_image(card_paths[0])

        # 5. Publishing
        comments = [copy_pkg["comment_1"], copy_pkg["comment_2"], copy_pkg["comment_3"]]
        threads_res = self.threads.publish_full_thread(
            main_text=copy_pkg["main_text"],
            comments=comments,
            image_url=public_image_url
        )

        # Record in DB
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        post_record = PostRecord(
            product_id=product.product_id,
            post_type="affiliate",
            platform="threads",
            main_text=copy_pkg["main_text"],
            comment_1=copy_pkg["comment_1"],
            comment_2=copy_pkg["comment_2"],
            comment_3=copy_pkg["comment_3"],
            image_paths=json.dumps(card_paths),
            platform_post_id=threads_res.get("platform_post_id"),
            status=threads_res.get("status", "simulated"),
            published_at=now_str
        )
        post_id = save_post_record(post_record)
        mark_product_posted(product.product_id)

        # Send Webhook Notification
        self.notify.send_post_alert(
            title=product.title,
            category=product.category,
            price=product.price,
            deeplink=deeplink,
            status=threads_res.get("status", "simulated")
        )

        save_log("INFO", "pipeline", f"Successfully completed affiliate posting cycle (Post #{post_id})")

        return {
            "success": True,
            "post_type": "affiliate",
            "post_id": post_id,
            "product": product.title,
            "main_text": copy_pkg["main_text"],
            "comments": comments,
            "cards": card_paths,
            "status": threads_res.get("status")
        }

    def _run_info_cycle(self) -> Dict[str, Any]:
        """Runs high-engagement non-affiliate post cycle."""
        category = random.choice(["생활용품", "아이디어", "자취꿀팁", "생산성"])
        copy_pkg = self.generator.generate_info_post(category=category)

        threads_res = self.threads.publish_full_thread(
            main_text=copy_pkg["main_text"],
            comments=[copy_pkg["comment_1"]] if copy_pkg.get("comment_1") else []
        )

        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        post_record = PostRecord(
            product_id=None,
            post_type="info",
            platform="threads",
            main_text=copy_pkg["main_text"],
            comment_1=copy_pkg["comment_1"],
            status=threads_res.get("status", "simulated"),
            published_at=now_str
        )
        post_id = save_post_record(post_record)

        save_log("INFO", "pipeline", f"Successfully completed organic info cycle (Post #{post_id})")
        return {
            "success": True,
            "post_type": "info",
            "post_id": post_id,
            "main_text": copy_pkg["main_text"],
            "comment_1": copy_pkg["comment_1"],
            "status": threads_res.get("status")
        }
