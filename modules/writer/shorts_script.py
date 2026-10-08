import random
import re
from typing import Dict, Any, List, Optional
from database.models import Product
from database.db import save_log
from modules.writer.llm_client import LLMClient


class ShortsScriptWriter:
    """
    30-Second Storytelling Script Writer:
    Adopts empathetic, persuasive, calm creator storytelling:
    1. Opening (0~6s): Recent daily event & relatable discomfort
    2. Problem (6~12s): Stress/crisis before having this item
    3. Solution (12~20s): Parcel arrival & instant relief/resolution
    4. Detail (20~25s): Accessibility for beginners/anyone
    5. Closing & CTA (25~30s): Conviction + Showroom #{item_num} action trigger
    """

    def __init__(self):
        self.llm = LLMClient()

    def generate_script(self, product: Product, item_num: int = 1) -> Dict[str, Any]:
        """Produces a 30-second persuasive storytelling script package."""
        # 1. Try LLM if API key is configured
        if self.llm.gemini_key or self.llm.openai_key:
            try:
                res = self._generate_with_llm(product, item_num)
                if res and res.get("narration"):
                    save_log("INFO", "shorts_script", f"AI LLM 30s storytelling script generated for #{item_num} {product.title[:15]}")
                    return res
            except Exception as e:
                save_log("WARNING", "shorts_script", f"LLM script gen failed, falling back to storytelling templates: {e}")

        # 2. Dynamic 30-Second Storytelling Template Engine
        return self._generate_storytelling_template(product, item_num)

    def _generate_with_llm(self, product: Product, item_num: int) -> Optional[Dict[str, Any]]:
        prompt = f"""
당신은 일상 속 불편을 풀어주는 숏폼 크리에이터입니다.
웃기기보다는, 왜 이 제품이 꼭 필요했는지를 깊이 공감하면서 사람들에게 진솔하게 설득을 주는 30초 숏폼 대본을 작성하세요.

[제품 정보]
- 제품명: {product.title}
- 카테고리: {product.category}
- 가격: {product.price:,}원
- 평점: {product.rating}점 (리뷰 {product.review_count:,}개)
- 쇼룸 번호: #{item_num}번

[대본 작성 조건]
1. 영상 길이: 28~32초 (나레이션 분량: 140~170자 내외, 차분하고 진솔한 일상 대화체)
2. 말투: 침착하고 진솔하게 대화하는 어조 ("~했거든요", "~하더라구요", "~만족스러워요")
3. 5단계 구성:
   - 오프닝 (0~6초): 최근 일상에서 겪은 불편한 사건 소개, 자극적 상황·숫자 비중 강조
   - 문제 상황 (6~12초): 이 제품이 없으면 겪을 수 있는 현실적인 불편·위기 묘사
   - 해결 방법 (12~20초): 택배 도착 후 이 제품으로 문제가 해결되는 실제 사용 경험 강조 ({product.price:,}원대 가성비)
   - 활용 디테일 (20~25초): 누구나 부담 없이 쓸 수 있는 디테일한 편의성 연결
   - 마무리 멘트 (25~30초): 행동 유도 ("자세한 구매 링크는 채널 프로필 쇼룸 {item_num}번 상품에서 확인하세요!")
4. 추가 요소: "이건 진짜 필요하겠다"라는 확신을 주는 추천 제목 5개 추천

다음 JSON 형식으로만 응답하세요:
{{
  "hook": "오프닝 15자 내외 자막",
  "narration": "AI 보이스가 읽을 전체 나레이션 전문 (140~170자)",
  "sub_1": "1단계 오프닝 핵심 자막",
  "sub_2": "2단계 문제 상황 공감 자막",
  "sub_3": "3단계 해결 및 가성비 자막 ({product.price:,}원)",
  "sub_4": "4단계 활용 디테일 자막",
  "sub_5": "5단계 프로필 쇼룸 #{item_num}번 확인 자막",
  "badge": "상단 뱃지 (예: 🔥 삶의 질 수직상승템)",
  "titles": ["추천 제목 1", "추천 제목 2", "추천 제목 3", "추천 제목 4", "추천 제목 5"]
}}
"""
        raw = self.llm.generate_copy(prompt, is_affiliate=True)
        if raw and "narration" in raw:
            cta = f"자세한 구매 링크는 채널 프로필 쇼룸 {item_num}번 상품에서 확인하세요!"
            narration = raw["narration"]
            if str(item_num) not in narration:
                narration = narration.rstrip(".! ") + f". {cta}"
            return {
                "hook": raw.get("hook", f"{product.title[:15]} 솔직후기"),
                "narration": narration,
                "sub_1": raw.get("sub_1", "매일 겪던 이 스트레스"),
                "sub_2": raw.get("sub_2", "원래는 진짜 불편했거든요"),
                "sub_3": raw.get("sub_3", f"{product.price:,}원대 실사용 혁신"),
                "sub_4": raw.get("sub_4", "누구나 부담 없이 간편 사용"),
                "sub_5": raw.get("sub_5", f"프로필 쇼룸 #{item_num}번 확인!"),
                "badge": raw.get("badge", f"🔥 일상 필수 #{item_num}번 꿀템"),
                "titles": raw.get("titles", [f"[#{item_num}] {product.title[:20]} 솔직후기"])
            }
        return None

    def _generate_storytelling_template(self, product: Product, item_num: int) -> Dict[str, Any]:
        """Dynamic 30-second storytelling template engine matching the user's 5-stage framework."""
        words = product.title.split()
        short_name = " ".join(words[:3]) if words else product.title[:12]
        price_str = f"{product.price:,}원"

        cta = f"자세한 구매 링크는 채널 프로필 쇼룸 {item_num}번 상품에서 확인하세요!"

        # Category: 생활 / 욕실 / 청소 / 주방
        if any(k in product.title for k in ["클리너", "배수구", "청소", "물때", "밀대", "압축봉", "분무기", "롤러", "돌돌이"]):
            opening = "며칠 전 대청소하다가 손목 나갈 뻔했는데 다행히 그날 도착한 택배가 살림을 살렸어요."
            problem = "매번 박박 문질러도 며칠만 지나면 냄새나고 찌든 때가 다시 올라와서 스트레스였거든요."
            solution = f"바로 이 {short_name}인데, {price_str}대에 가볍게 쓰기만 해도 때가 싹 씻겨서 속이 다 시원하더라구요."
            detail = f"살림 초보자도 힘 안 들이고 매일 쓸 수 있어서 왜 평점이 {product.rating}점인지 알겠어요."
            hook_text = "살림 피로도 반으로 줄여준\n진짜 필요했던 인생템"
            sub_1 = "대청소 스트레스 단번에 끝냄"
            sub_2 = "매번 문질러도 다시 생기던 때"
            sub_3 = f"{price_str}대 실사용 해결"
            sub_4 = "초보자도 힘 안 들이고 사용"
            badge = "✨ 살림 스트레스 종결템"
            titles = [
                f"[#{item_num}] 주말마다 박박 문지르던 살림, 이거 하나로 끝냈습니다",
                f"[#{item_num}] 살림은 장비빨이라더니... {short_name} 솔직 사용기",
                f"[#{item_num}] 청소 스트레스 90% 줄여준 {price_str}대 가성비 꿀템",
                f"[#{item_num}] 진작 쓸 걸 후회한 {short_name} 추천 후기",
                f"[#{item_num}] 손목 나갈 뻔했던 살림러를 구원한 인생템 #shorts"
            ]

        # Category: 아이디어 / 데스크 / 노트북 / 선정리
        elif any(k in product.title for k in ["케이블", "마그네틱", "거치대", "노트북", "홀더", "태블릿", "압축기", "데스크"]):
            opening = "며칠 전 일하다가 책상 위가 너무 어수선해서 집중이 안 됐는데 이 택배 받고 분위기가 싹 바뀌었어요."
            problem = "선은 매번 엉키고 자세도 구부정해져서 오후만 되면 목이랑 어깨가 뻐근했거든요."
            solution = f"바로 이 {short_name}인데, {price_str}대에 공간도 깔끔하게 정돈되고 자세까지 탄탄하게 잡아주더라구요."
            detail = "작업 공간 좁은 분들이나 학생, 직장인 누구나 부담 없이 쓸 수 있어 꽤 만족스러워요."
            hook_text = "책상 위 지저분함 한 번에 해결한\n데스크 세팅 끝판왕"
            sub_1 = "어수선한 책상 완벽 정돈"
            sub_2 = "매번 엉키고 자세도 무너지던 날"
            sub_3 = f"{price_str}대 작업 효율 2배 상승"
            sub_4 = "누구나 깔끔하게 데스크 정돈"
            badge = "💻 데스크 삶의 질 상승템"
            titles = [
                f"[#{item_num}] 지저분한 책상 위, 이 작은 거 하나로 2배 넓어졌습니다",
                f"[#{item_num}] {short_name} 써보고 업무 집중도가 달라졌어요",
                f"[#{item_num}] 거북목과 선 엉킴 단번에 해결한 {price_str}대 데스크템",
                f"[#{item_num}] 왜 다들 데스크 필수템이라고 극찬하는지 알겠네요",
                f"[#{item_num}] 진작 살 걸 후회한 {short_name} 솔직리뷰 #shorts"
            ]

        # Category: 반려동물 / 펫
        elif any(k in product.title for k in ["반려", "강아지", "고양이", "펫", "브러시", "매트", "노즈워크", "정수기", "털"]):
            opening = "외출하고 돌아올 때마다 우리 아이 불안해하는 모습 보고 마음이 늘 무거웠거든요."
            problem = "털 날림 청소도 힘들고 혼자 있는 시간이 길어지니까 스트레스를 많이 받는 게 보였어요."
            solution = f"그때 도착한 이 {short_name} 써봤는데, {price_str}대에 호기심도 채워주고 안정감까지 찾아주더라구요."
            detail = f"반려동물 키우는 초보 집사도 안심하고 매일 쓸 수 있어서 평점 {product.rating}점인 이유를 알겠어요."
            hook_text = "혼자 있는 댕냥이 스트레스\n단번에 풀어준 꿀템"
            sub_1 = "혼자 있는 아이 볼 때마다 걱정"
            sub_2 = "털 날림과 분리불안 스트레스"
            sub_3 = f"{price_str}대로 집사 걱정 끝"
            sub_4 = "매일 안심하고 쓰는 필수템"
            badge = "🐾 댕냥이 집사 필수템"
            titles = [
                f"[#{item_num}] 외출할 때 불안해하던 우리 아이, 이걸로 해결했습니다",
                f"[#{item_num}] 집사 삶의 질 수직 상승시켜 준 {short_name} 후기",
                f"[#{item_num}] 혼자서도 꼬리 흔들며 잘 노는 {price_str}대 꿀템",
                f"[#{item_num}] 누적 리뷰 {product.review_count:,}개 검증된 반려용품",
                f"[#{item_num}] 털 날림과 스트레스 동시에 잡아준 인생템 #shorts"
            ]

        # Category: 다이어트 / 식단
        elif any(k in product.title for k in ["다이어트", "저당", "알룰로스", "소스", "단백질", "쉐이커", "쫀드기", "간식", "식단"]):
            opening = "며칠 전 닭가슴살만 먹다가 입 터질 뻔했는데 마침 도착한 택배가 식단 위기를 넘겨줬어요."
            problem = "맛없는 식단 억지로 참다 보면 결국 밤에 폭식하게 돼서 죄책감만 들었거든요."
            solution = f"바로 이 {short_name}인데, {price_str}대에 당류 칼로리 부담 없이 맛을 꽉 채워줘서 너무 든든하더라구요."
            detail = "식단 초보자도 질리지 않고 건강하게 유지할 수 있어서 꽤 만족스러워요."
            hook_text = "식단 관리 중에 입 터짐 방지\n제대로 해준 다이어트 꿀템"
            sub_1 = "식단 중 입 터질 뻔했던 날"
            sub_2 = "억지로 참다가 폭식하던 악순환"
            sub_3 = f"{price_str}대 칼로리 부담 제로"
            sub_4 = "초보자도 질리지 않고 식단 유지"
            badge = "🥗 다이어터 식단 구원템"
            titles = [
                f"[#{item_num}] 맛있게 먹으면서 살 빼는 거, 진짜 가능하더라구요",
                f"[#{item_num}] 식단 스트레스와 입 터짐 단번에 막아준 {short_name}",
                f"[#{item_num}] {price_str}대로 다이어트 식단 삶의 질 2배 올려줌",
                f"[#{item_num}] 다이어터들 사이에서 재구매율 1위인 이유",
                f"[#{item_num}] 닭가슴살 지겨울 때 무조건 쟁여두는 필수템 #shorts"
            ]

        # Default Storytelling
        else:
            opening = "일상에서 매번 사소하게 불편했던 순간들이 있었는데, 이번에 써본 제품이 그 고민을 딱 해결해줬어요."
            problem = "그냥 참고 살기엔 매일 마주치는 불편함이라 은근히 피로도가 쌓였거든요."
            solution = f"바로 이 {short_name}인데, {price_str}대에 써보자마자 왜 다들 추천하는지 확실히 알겠더라구요."
            detail = f"누구나 쉽게 쓸 수 있고 내구성도 탄탄해서 실사용 만족도가 꽤 높아요."
            hook_text = "일상 속 진짜 필요했던 이유\n내돈내산 솔직 리뷰"
            sub_1 = "매일 마주치던 사소한 불편"
            sub_2 = "참고 살다 보니 쌓이던 피로감"
            sub_3 = f"{price_str}대 실사용 만족도 최고"
            sub_4 = "누구나 쉽게 쓰는 실용템"
            badge = f"🔥 숏츠 속 #{item_num}번 꿀템"
            titles = [
                f"[#{item_num}] 진작 쓸 걸 후회한 {short_name} 솔직한 리뷰",
                f"[#{item_num}] {price_str}대로 일상 불편 싹 해결해 준 꿀템",
                f"[#{item_num}] 이건 진짜 필요하겠다 싶어 써본 실사용기",
                f"[#{item_num}] 평점 {product.rating}점으로 검증된 인생템",
                f"[#{item_num}] 일상의 질을 바꿔준 {short_name} #shorts"
            ]

        # Assemble full 30-second narration (~140-160 Korean characters)
        full_narration = f"{opening} {problem} {solution} {detail} {cta}"

        return {
            "hook": hook_text,
            "narration": full_narration,
            "sub_1": sub_1,
            "sub_2": sub_2,
            "sub_3": sub_3,
            "sub_4": sub_4,
            "sub_5": f"프로필 쇼룸 #{item_num}번 확인!",
            "badge": badge,
            "titles": titles
        }
