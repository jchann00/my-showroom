import json
import re
import requests
from typing import Dict, Any, Optional
from config.settings import load_config
from database.db import save_log
from modules.writer.prompts import SYSTEM_PROMPT_AFFILIATE, SYSTEM_PROMPT_INFO


class LLMClient:
    """Multi-provider LLM client with Gemini, OpenAI, Claude, and built-in template fallback."""

    def __init__(self):
        self.reload_config()

    def reload_config(self):
        cfg = load_config()
        self.llm_cfg = cfg.get("llm", {})
        self.provider = self.llm_cfg.get("provider", "gemini")
        self.gemini_key = self.llm_cfg.get("gemini_api_key", "")
        self.openai_key = self.llm_cfg.get("openai_api_key", "")
        self.claude_key = self.llm_cfg.get("claude_api_key", "")
        self.model_name = self.llm_cfg.get("model_name", "gemini-2.5-flash")

    def generate_copy(self, prompt_text: str, is_affiliate: bool = True) -> Dict[str, str]:
        """Generate post copy using configured LLM or fallback."""
        self.reload_config()
        system_prompt = SYSTEM_PROMPT_AFFILIATE if is_affiliate else SYSTEM_PROMPT_INFO

        # Try Gemini
        if self.gemini_key and (self.provider == "gemini" or not self.openai_key):
            result = self._call_gemini(system_prompt, prompt_text)
            if result:
                return result

        # Try OpenAI
        if self.openai_key and (self.provider == "openai" or not self.gemini_key):
            result = self._call_openai(system_prompt, prompt_text)
            if result:
                return result

        # Try Claude
        if self.claude_key and self.provider == "claude":
            result = self._call_claude(system_prompt, prompt_text)
            if result:
                return result

        save_log("INFO", "llm", "No external LLM key active. Using high-converting built-in copy template.")
        return self._generate_fallback(prompt_text, is_affiliate)

    def _call_gemini(self, system_prompt: str, user_prompt: str) -> Optional[Dict[str, str]]:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model_name}:generateContent?key={self.gemini_key}"
        payload = {
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": f"{system_prompt}\n\n[상품 및 요청 정보]\n{user_prompt}\n\n반드시 JSON 형식으로만 응답하세요."}]
                }
            ],
            "generationConfig": {
                "temperature": 0.7,
                "responseMimeType": "application/json"
            }
        }
        try:
            res = requests.post(url, json=payload, timeout=20)
            if res.status_code == 200:
                data = res.json()
                text = data["candidates"][0]["content"]["parts"][0]["text"]
                return self._parse_json_response(text)
            else:
                save_log("ERROR", "llm", f"Gemini API error ({res.status_code}): {res.text}")
        except Exception as e:
            save_log("ERROR", "llm", f"Gemini API exception: {e}")
        return None

    def _call_openai(self, system_prompt: str, user_prompt: str) -> Optional[Dict[str, str]]:
        url = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.openai_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": "gpt-4o-mini",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "response_format": {"type": "json_object"},
            "temperature": 0.7
        }
        try:
            res = requests.post(url, headers=headers, json=payload, timeout=20)
            if res.status_code == 200:
                data = res.json()
                text = data["choices"][0]["message"]["content"]
                return self._parse_json_response(text)
            else:
                save_log("ERROR", "llm", f"OpenAI API error ({res.status_code}): {res.text}")
        except Exception as e:
            save_log("ERROR", "llm", f"OpenAI API exception: {e}")
        return None

    def _call_claude(self, system_prompt: str, user_prompt: str) -> Optional[Dict[str, str]]:
        url = "https://api.anthropic.com/v1/messages"
        headers = {
            "x-api-key": self.claude_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }
        payload = {
            "model": "claude-3-5-haiku-20241022",
            "max_tokens": 1000,
            "system": system_prompt,
            "messages": [{"role": "user", "content": user_prompt}]
        }
        try:
            res = requests.post(url, headers=headers, json=payload, timeout=20)
            if res.status_code == 200:
                data = res.json()
                text = data["content"][0]["text"]
                return self._parse_json_response(text)
            else:
                save_log("ERROR", "llm", f"Claude API error: {res.text}")
        except Exception as e:
            save_log("ERROR", "llm", f"Claude API exception: {e}")
        return None

    def _parse_json_response(self, text: str) -> Optional[Dict[str, str]]:
        try:
            # Extract json block if surrounded by markdown
            clean_text = re.sub(r"^```(?:json)?\s*", "", text.strip())
            clean_text = re.sub(r"\s*```$", "", clean_text)
            return json.loads(clean_text)
        except Exception as e:
            save_log("ERROR", "llm", f"Failed to parse LLM JSON: {e}")
            return None

    def _generate_fallback(self, prompt_text: str, is_affiliate: bool) -> Dict[str, str]:
        """High-converting battle-tested fallback templates adhering to all guide principles."""
        if not is_affiliate:
            return {
                "main_text": (
                    "자취 3년 차 되면서 깨달은 건데\n"
                    "청소는 장비빨이 맞습니다.\n\n"
                    "괜히 손목 나가면서 박박 문지르지 말고\n"
                    "약품이랑 도구 제대로 쓰니까\n"
                    "주말에 청소하는 시간 1시간 줄었네요.\n\n"
                    "다들 청소할 때 꼭 쓰는 꿀팁 있으신가요?"
                ),
                "comment_1": "싱크대 물때는 과탄산소다보다 폼 클리너가 곰팡이까지 싹 잡아서 훨씬 편하더라고요.",
                "comment_2": "",
                "comment_3": "",
                "card_headline": "자취 3년 차가 깨달은 살림 꿀팁",
                "card_subtext": "주말 청소 시간 절반으로 줄여준 방법"
            }

        # Check keyword in prompt_text for tailored copy
        if "배수구" in prompt_text or "클리너" in prompt_text or "청소" in prompt_text:
            return {
                "main_text": (
                    "싱크대 배수구 청소할 때마다\n"
                    "칫솔 들고 문지르는 거 진짜 고역이었는데.\n\n"
                    "유튜브에서 본 폼 클리너 반신반의하고 뿌려봤거든요.\n"
                    "물만 뿌렸는데 찌든 물때 싹 내려가는 거 보고 허탈했습니다.\n\n"
                    "지금까지 뭐 하러 땀 흘리면서 닦았나 싶네요.\n"
                    "정보 궁금하신 분들은 첫 댓글에 남겨둘게요."
                ),
                "comment_1": (
                    "이 포스팅은 쿠팡 파트너스 활동의 일환으로, 이에 따른 일정액의 수수료를 제공받습니다.\n"
                    "홈스타 배수구 폼 클리너 2개 세트 만 원대이고 로켓배송이라 내일 바로 와요.\n"
                    "{deeplink}"
                ),
                "comment_2": "뜨거운 물 붓지 말고 그냥 찬물에 15분 방치하는 게 거품 더 오래 붙어있어서 청소 잘 됩니다. {deeplink}",
                "comment_3": "장갑 안 끼고 뿌리기만 하면 돼서 살림 피로도 확 줄었어요. {deeplink}",
                "card_headline": "싱크대 찌든때 3초 컷 꿀템",
                "card_subtext": "칫솔로 문지르지 마세요, 뿌리기만 하면 끝"
            }
        elif "소스" in prompt_text or "다이어트" in prompt_text or "알룰로스" in prompt_text:
            return {
                "main_text": (
                    "식단 할 때 스리라차 소스만 먹다 물려서\n"
                    "저당 데리야끼 소스로 바꿨습니다.\n\n"
                    "당류 1g인데 밖에서 파는 덮밥 소스 맛 그대로 나네요.\n"
                    "닭가슴살 볶음밥에 이거 두 스푼 넣으니까\n"
                    "식단 스트레스 바로 끝났습니다.\n\n"
                    "쟁여두고 먹는 건 댓글에 달아둘게요."
                ),
                "comment_1": (
                    "이 포스팅은 쿠팡 파트너스 활동의 일환으로, 이에 따른 일정액의 수수료를 제공받습니다.\n"
                    "마이노멀 알룰로스 데리야끼 소스 만 원대 로켓배송.\n"
                    "{deeplink}"
                ),
                "comment_2": "소고기 우둔살이나 두부 부침에 살짝 둘러도 진짜 감칠맛 대박입니다. {deeplink}",
                "comment_3": "식단 오래 지속하려면 소스는 맛있는 거 써야 돼요. {deeplink}",
                "card_headline": "당류 1g 데리야끼 소스 실후기",
                "card_subtext": "닭가슴살 식단 스트레스 단번에 끝낸 비결"
            }
        elif "털" in prompt_text or "펫" in prompt_text or "고양이" in prompt_text or "강아지" in prompt_text:
            return {
                "main_text": (
                    "환절기마다 온 집안에 털 날려서\n"
                    "테이프 돌돌이 하루에 3통씩 썼는데요.\n\n"
                    "실리콘 브러시로 슥 긁으니까\n"
                    "카펫이랑 이불에 박힌 털 싹 뭉쳐서 나옵니다.\n\n"
                    "물로 헹구면 무한 재사용이라 돌돌이 값 굳었네요.\n"
                    "어디서 샀는지는 댓글에 둘게요."
                ),
                "comment_1": (
                    "이 포스팅은 쿠팡 파트너스 활동의 일환으로, 이에 따른 일정액의 수수료를 제공받습니다.\n"
                    "실리콘 털 제거 브러시 만 원대 로켓배송으로 바로 옵니다.\n"
                    "{deeplink}"
                ),
                "comment_2": "물티슈로 닦는 것보다 물로 한번 헹궈서 털어내는 게 제일 깔끔해요. {deeplink}",
                "comment_3": "집사님들이나 견주분들은 진짜 필수템입니다. {deeplink}",
                "card_headline": "박힌 털 싹쓸이 실리콘 브러시",
                "card_subtext": "돌돌이 쓰레기 안 나오는 영구 다회용 필수템"
            }
        else:
            return {
                "main_text": (
                    "책상 위에 충전선 늘어져 있는 거 볼 때마다\n"
                    "은근히 신경 쓰이고 지저분했는데.\n\n"
                    "자석형 케이블 홀더 붙여놓으니까\n"
                    "근처만 가도 착 달라붙어서 정리 끝이네요.\n\n"
                    "책상 깔끔해지니까 집중도 잘 됩니다.\n"
                    "정보 궁금하신 분들은 첫 댓글에 남겨둘게요."
                ),
                "comment_1": (
                    "이 포스팅은 쿠팡 파트너스 활동의 일환으로, 이에 따른 일정액의 수수료를 제공받습니다.\n"
                    "마그네틱 자석 케이블 홀더 만 원대 로켓배송.\n"
                    "{deeplink}"
                ),
                "comment_2": "모니터 뒤나 책상 프레임 쪽에 붙이면 선이 아예 안 보여서 훨씬 깔끔합니다. {deeplink}",
                "comment_3": "선 밟거나 꼬이는 일 없어서 너무 만족해요. {deeplink}",
                "card_headline": "데스크테리어 끝판왕 자석 홀더",
                "card_subtext": "지저분한 충전선 착 붙여서 1초 만에 정리"
            }
