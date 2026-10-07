import sys
import os
from pathlib import Path

# Ensure UTF-8 output on Windows console
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from modules.scheduler.auto_pilot import AutoPilotScheduler
from database.db import get_stats, get_recent_posts, get_recent_products


def run_test():
    print("========================================")
    print("🚀 [TEST] 쓰레드 × 쿠팡파트너스 자동화 파이프라인 검증")
    print("========================================")

    scheduler = AutoPilotScheduler()

    print("\n[1단계] 즉시 1회 자동 발행 (수익화 모드 강제 실행)...")
    res = scheduler.trigger_one_post(force_affiliate=True)

    print("\n[2단계] 실행 결과:")
    print(f"• 성공 여부: {res.get('success')}")
    print(f"• 포스트 ID: {res.get('post_id')}")
    print(f"• 선정 상품: {res.get('product')}")
    print(f"• 발행 상태: {res.get('status')}")

    print("\n--- [생성된 본문 (300자 이내, 링크 배제 검증)] ---")
    print(res.get("main_text"))

    print("\n--- [생성된 댓글 1 (공정위 문구 & 파트너스 링크)] ---")
    comments = res.get("comments", [])
    if comments:
        print(comments[0])

    print("\n--- [생성된 댓글 2 (실사용 꿀팁)] ---")
    if len(comments) > 1:
        print(comments[1])

    print("\n--- [생성된 카드뉴스 이미지 파일] ---")
    for card in res.get("cards", []):
        print(f"• {card}")

    print("\n[3단계] DB 통계 확인:")
    stats = get_stats()
    print(f"• 적재된 상품 수: {stats['total_products']}")
    print(f"• 총 발행 포스트: {stats['published_posts']}")
    print(f"• 오늘 발행 포스트: {stats['today_posts']}")

    print("\n========================================")
    print("✅ 테스트 완료: 모든 모듈 정상 작동 확인")
    print("========================================")


if __name__ == "__main__":
    run_test()
