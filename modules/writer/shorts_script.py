import random
import re
from typing import Dict, Any, List
from database.models import Product
from database.db import save_log
from modules.writer.llm_client import LLMClient


class ShortsScriptWriter:
    """Generates unique, high-converting, viral YouTube Shorts scripts tailored to each product."""

    def __init__(self):
        self.llm = LLMClient()

    def generate_script(self, product: Product, item_num: int = 1) -> Dict[str, Any]:
        """
        Produces a custom script package:
        - hook: 0-3 sec visual headline
        - narration: 15-sec full speech narration (100-130 Korean chars)
        - subtitle_lines: 3 sequential subtitle cards
        - badge: top badge tag
        """
        # Try LLM first if external key available
        if self.llm.gemini_key or self.llm.openai_key:
            try:
                res = self._generate_with_llm(product, item_num)
                if res and res.get("narration"):
                    save_log("INFO", "shorts_script", f"AI LLM generated custom script for #{item_num} {product.title[:15]}")
                    return res
            except Exception as e:
                save_log("WARNING", "shorts_script", f"LLM script gen failed, falling back to dynamic template: {e}")

        # Dynamic Smart Category Template Engine
        return self._generate_dynamic_template(product, item_num)

    def _generate_with_llm(self, product: Product, item_num: int) -> Dict[str, Any]:
        prompt = f"""
당신은 유튜브 숏츠 100만 조회수 바이럴 전문 작가입니다.
아래 쿠팡 로켓배송 상품의 15초 쇼츠 나레이션 대본을 작성하세요.

[상품 정보]
- 상품명: {product.title}
- 카테고리: {product.category}
- 가격: {product.price:,}원
- 평점: {product.rating}점 (리뷰 {product.review_count:,}개)
- 쇼룸 번호: #{item_num}번

[필수 규칙]
1. 0~3초: 스크롤을 즉시 멈추게 하는 충격/공감형 후킹 (질문 또는 강력한 주장)
2. 3~11초: 이 상품만의 구체적인 특징과 일상이 편리해지는 이유 ({product.price:,}원 가성비 강조)
3. 11~15초: "자세한 구매 링크는 채널 프로필 쇼룸 {item_num}번 상품에서 확인하세요!" 필수 포함
4. 나레이션 길이는 100~130자 내외 (말하는 속도 기준 12~14초 분량)

다음 JSON 형식으로만 응답하세요:
{{
  "hook": "영상 상단에 띄울 15자 내외 후킹 문구",
  "narration": "AI 보이스가 읽을 전체 나레이션 전문",
  "sub_1": "초반 0~5초 자막 요약",
  "sub_2": "중반 5~10초 자막 요약",
  "sub_3": "후반 10~15초 자막 요약",
  "badge": "상단 뱃지 (예: 🔥 품절대란 꿀템)"
}}
"""
        raw = self.llm.generate_copy(prompt, is_affiliate=True)
        if raw and "narration" in raw:
            # Ensure showroom CTA is strictly included
            cta = f"자세한 구매 링크는 채널 프로필 쇼룸 {item_num}번 상품에서 확인하세요!"
            narration = raw["narration"]
            if str(item_num) not in narration:
                narration = narration.rstrip(".! ") + f". {cta}"
            return {
                "hook": raw.get("hook", f"{product.title[:15]} 솔직후기"),
                "narration": narration,
                "sub_1": raw.get("sub_1", raw.get("hook", "")),
                "sub_2": raw.get("sub_2", f"{product.price:,}원대 실사용 가성비"),
                "sub_3": raw.get("sub_3", f"프로필 쇼룸 #{item_num}번 확인!"),
                "badge": raw.get("badge", f"🔥 숏츠 속 #{item_num}번 꿀템")
            }
        return None

    def _generate_dynamic_template(self, product: Product, item_num: int) -> Dict[str, Any]:
        """Category-specific dynamic template engine with randomized hooks & angles."""
        title_short = product.title.split()[0:3]
        short_name = " ".join(title_short) if title_short else product.title[:12]
        cat = product.category
        price_str = f"{product.price:,}원"

        cta = f"자세한 구매 링크는 채널 프로필 쇼룸 {item_num}번 상품에서 확인하세요!"

        # Category: 다이어트 / 식품
        if any(k in product.title for k in ["곤약", "다이어트", "단백질", "저당", "알룰로스", "소스", "식단", "간식"]):
            hooks = [
                ("식단 중에 입 터질 뻔한 분들\n지금 3초만 집중하세요", "입 터짐 방지 1위 다이어트 꿀템"),
                ("맛있게 먹으면서 살 빼는 거\n진짜 가능했습니다", "다이어터들 사이 난리 난 간식"),
                ("칼로리 걱정 없이 씹는 맛\n이거 하나로 끝냈습니다", "식단 스트레스 종결템")
            ]
            bodies = [
                f"{short_name}! {price_str}대에 칼로리 부담 전혀 없고 식감도 쫄깃해서 입 터짐 방지 제대로 됩니다.",
                f"{short_name}인데 성분도 착하고 속도 편안해서 다이어터들 사이에서 재구매 1위인 이유가 있네요.",
                f"{price_str}대 가성비에 맛까지 완벽해서 닭가슴살 식단 스트레스 단번에 날려버렸습니다."
            ]
            badge = "🥗 다이어터 필수 꿀템"

        # Category: 반려동물 / 펫
        elif any(k in product.title for k in ["강아지", "고양이", "반려", "펫", "노즈워크", "털", "배변", "간식"]):
            hooks = [
                ("우리 집 댕댕이가 이것만 보면\n꼬리를 멈추질 않아요", "반려인 99%가 만족한 꿀템"),
                ("외출할 때 분리불안 심한 아이들\n이거 꼭 써보세요", "강아지 스트레스 해소 끝판왕"),
                ("털 날림이랑 청소 스트레스\n한 번에 끝냈습니다", "집사 삶의 질 수직 상승템")
            ]
            bodies = [
                f"{short_name}! {price_str}대인데 호기심 자극에 스트레스까지 싹 풀어줘서 집사 피로도가 확 줄었습니다.",
                f"실제 후기 {product.review_count:,}개로 검증된 {short_name}! 혼자서도 너무 잘 놀아서 안심입니다.",
                f"{price_str}대로 부담 없는데 튼튼하고 안전해서 매일매일 쓰는 최애 반려템입니다."
            ]
            badge = "🐾 댕냥이 최애 꿀템"

        # Category: 아이디어 / 데스크 / 전자기기
        elif any(k in product.title for k in ["거치대", "노트북", "충전", "케이블", "마우스", "키보드", "데스크", "독서대", "태블릿"]):
            hooks = [
                ("책상 위 지저분하고 목 아프던 분들\n이거 3초만 보세요", "데스크 세팅 끝판왕"),
                ("이 작은 거 하나 바꿨더니\n작업 효율이 2배 올랐습니다", "생산성 수직 상승 꿀템"),
                ("아직도 거북목으로 고생하세요?\n진작 쓸 걸 후회했습니다", "목·어깨 피로도 해소템")
            ]
            bodies = [
                f"{short_name}! {price_str}대에 각도 조절도 완벽하고 튼튼해서 책상이 두 배로 넓어집니다.",
                f"{price_str}대 가성비에 흔들림 없이 탄탄해서 노트북이랑 태블릿 쓰시는 분들 필수템입니다.",
                f"공간 차지 없이 깔끔하게 정리되고 자세까지 바르게 잡아줘서 일할 때 피로감이 확 줄어듭니다."
            ]
            badge = "💻 데스크 생산성 꿀템"

        # Category: 생활 / 주방 / 욕실 / 청소
        elif any(k in product.title for k in ["클리너", "청소", "배수구", "물때", "밀대", "압축봉", "정리", "주방", "욕실"]):
            hooks = [
                ("살림은 장비빨이라는 말\n이거 써보고 뼈저리게 느꼈습니다", "살림 피로도 절반 단축"),
                ("주말마다 박박 문지르던 시절\n이거 하나로 끝났습니다", "청소 시간 3초 컷 꿀템"),
                ("아직도 손목 나가면서 청소하세요?\n진짜 신세계입니다", "주부들 극찬 살림 꿀템")
            ]
            bodies = [
                f"{short_name}! {price_str}대에 뿌리고 헹구기만 하면 찌든 때가 싹 씻겨 내려갑니다.",
                f"{price_str}대 로켓배송에 살림 피로도 확 줄여주는 필수템! 실제 평점 {product.rating}점인 이유가 있네요.",
                f"힘들게 문지를 필요 없이 간편하게 관리되니까 주말 여유 시간이 확 늘어났습니다."
            ]
            badge = "✨ 살림 극락 꿀템"

        # Default General Category
        else:
            hooks = [
                (f"실제 써보고 너무 만족해서\n지인들에게 추천한 꿀템", f"{product.title[:15]} 실사용 후기"),
                ("가성비에 품질까지 잡은 꿀템\n찾고 계셨다면 주목하세요", "평점 4.5+ 검증 완료"),
                ("삶의 질 수직 상승시켜 준\n쿠팡 로켓배송 인생템", "내돈내산 솔직 리뷰")
            ]
            bodies = [
                f"{short_name}! {price_str}대에 실제 리뷰 {product.review_count:,}개로 검증된 알짜배기 아이템입니다.",
                f"{price_str}대 가격 대비 마감과 내구성이 뛰어나서 매일매일 만족하면서 쓰고 있습니다.",
                f"로켓배송으로 주문하면 내일 바로 도착하고 실사용 만족도 {product.rating}점으로 압도적입니다."
            ]
            badge = f"🔥 숏츠 속 #{item_num}번 꿀템"

        hook_text, sub_1 = random.choice(hooks)
        body_text = random.choice(bodies)

        full_narration = f"{hook_text.replace(chr(10), ' ')}. {body_text} {cta}"

        return {
            "hook": hook_text,
            "narration": full_narration,
            "sub_1": sub_1,
            "sub_2": f"{price_str} (★ {product.rating}점)",
            "sub_3": f"프로필 링크 쇼룸 [#{item_num}번]",
            "badge": badge
        }
