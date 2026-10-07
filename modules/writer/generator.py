import re
from typing import Dict, Any, Tuple
from database.models import Product, PostRecord
from database.db import save_log
from modules.writer.llm_client import LLMClient

FTC_DISCLOSURE = "이 포스팅은 쿠팡 파트너스 활동의 일환으로, 이에 따른 일정액의 수수료를 제공받습니다."


class PostGenerator:
    """Generates fully compliant Threads & Instagram post contents."""

    def __init__(self):
        self.llm = LLMClient()

    def generate_affiliate_post(self, product: Product, deeplink: str) -> Dict[str, Any]:
        """Generate high-converting 5-element post package for a product."""
        user_prompt = (
            f"카테고리: {product.category}\n"
            f"상품명: {product.title}\n"
            f"가격: {product.price:,}원\n"
            f"평점: {product.rating}점 (리뷰 {product.review_count:,}개)\n"
            f"로켓배송: {'가능' if product.is_rocket else '불가'}\n"
            f"파트너스 링크: {deeplink}\n"
            f"원칙: 문제 해결/전후비교/실사용 디테일 위주로 본문 300자 이내 작성"
        )

        raw = self.llm.generate_copy(user_prompt, is_affiliate=True)
        return self._sanitize_and_finalize(raw, deeplink, product)

    def generate_info_post(self, category: str = "생활용품") -> Dict[str, Any]:
        """Generate non-affiliate high-engagement post (for 1:3 anti-ban ratio)."""
        user_prompt = f"카테고리: {category} 관련 일상 속 꿀팁, 공감대 형성되는 살림/생산성 이야기"
        raw = self.llm.generate_copy(user_prompt, is_affiliate=False)

        # Info posts don't have affiliate links
        main_text = self._strip_links(raw.get("main_text", ""))
        return {
            "main_text": main_text,
            "comment_1": raw.get("comment_1", ""),
            "comment_2": "",
            "comment_3": "",
            "card_headline": raw.get("card_headline", f"{category} 꿀팁"),
            "card_subtext": raw.get("card_subtext", "알아두면 유용한 일상 노하우")
        }

    def _sanitize_and_finalize(self, raw: Dict[str, str], deeplink: str, product: Product) -> Dict[str, Any]:
        """Enforces shadowban prevention and mandatory FTC compliance."""
        main_text = raw.get("main_text", "")
        # Rule: NO links in main body
        main_text = self._strip_links(main_text)

        # Enforce <= 300 characters
        if len(main_text) > 300:
            lines = [l for l in main_text.split("\n") if l.strip()]
            trimmed = ""
            for line in lines:
                if len(trimmed) + len(line) + 2 < 280:
                    trimmed += line + "\n\n"
            if not trimmed.endswith("댓글에 남겨둘게요.") and not trimmed.endswith("댓글에 둘게요."):
                trimmed += "자세한 건 댓글에 남겨둘게요."
            main_text = trimmed.strip()

        # Rule: FTC clause in Comment 1
        c1 = raw.get("comment_1", "")
        if FTC_DISCLOSURE not in c1:
            c1 = f"{FTC_DISCLOSURE}\n{c1}"

        # Inject deeplink into comments if not present
        if "{deeplink}" in c1:
            c1 = c1.replace("{deeplink}", deeplink)
        elif deeplink not in c1:
            c1 = f"{c1}\n{deeplink}"

        c2 = raw.get("comment_2", "")
        if c2:
            if "{deeplink}" in c2:
                c2 = c2.replace("{deeplink}", deeplink)
            elif deeplink not in c2:
                c2 = f"{c2} {deeplink}"

        c3 = raw.get("comment_3", "")
        if c3:
            if "{deeplink}" in c3:
                c3 = c3.replace("{deeplink}", deeplink)
            elif deeplink not in c3:
                c3 = f"{c3} {deeplink}"

        return {
            "main_text": main_text.strip(),
            "comment_1": c1.strip(),
            "comment_2": c2.strip(),
            "comment_3": c3.strip(),
            "card_headline": raw.get("card_headline", f"실제 써보고 놀란 {product.title[:12]}"),
            "card_subtext": raw.get("card_subtext", f"{product.price:,}원 로켓배송 실사용 후기")
        }

    def _strip_links(self, text: str) -> str:
        """Removes any URLs or domains from text to prevent shadowbans."""
        url_pattern = r"(https?://\S+|www\.\S+|coupang\.com\S*)"
        return re.sub(url_pattern, "", text).strip()
