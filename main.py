import sys
import os
import argparse
from pathlib import Path

# Ensure UTF-8 output on Windows console
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

import uvicorn
from database.db import init_db, save_log
from config.settings import load_config


import socket

def find_available_port(start_port: int = 8080) -> int:
    port = start_port
    while port < 9000:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(("127.0.0.1", port)) != 0:
                return port
        port += 1
    return start_port


def main():
    parser = argparse.ArgumentParser(description="Threads & Coupang Partners Full Automation Engine")
    parser.add_argument("--host", default="127.0.0.1", help="Host IP to bind web dashboard")
    parser.add_argument("--port", type=int, default=None, help="Port to bind web dashboard")
    parser.add_argument("--test", action="store_true", help="Run 1-cycle Threads test immediately and exit")
    parser.add_argument("--test-shorts", action="store_true", help="Run 1-cycle Shorts & Showroom test immediately and exit")
    args = parser.parse_args()

    # Ensure DB initialized
    init_db()

    if args.test:
        from modules.scheduler.auto_pilot import AutoPilotScheduler
        print("🚀 [CLI] 즉시 1회 쓰레드 자동 발행 테스트를 실행합니다...")
        scheduler = AutoPilotScheduler()
        res = scheduler.trigger_one_post(force_affiliate=True)
        print(f"✅ 실행 완료: {res}")
        return

    if args.test_shorts:
        from modules.scheduler.auto_pilot import AutoPilotScheduler
        print("🎬 [CLI] 15초 숏츠 영상 제작 및 모바일 쇼룸 갱신 테스트를 실행합니다...")
        scheduler = AutoPilotScheduler()
        res = scheduler.trigger_shorts_cycle()
        print(f"✅ 실행 완료: {res}")
        return

    start_port = args.port or 8080
    bind_port = find_available_port(start_port)

    print("===================================================================")
    print("🤖 [AutoThreads AI] 인스타그램 & 쓰레드 쿠팡파트너스 무인 자동화 엔진")
    print(f"🌐 웹 관제 대시보드 접속 주소: http://{args.host}:{bind_port}")
    print("===================================================================")
    save_log("INFO", "main", f"System started on http://{args.host}:{bind_port}")

    # Launch browser automatically
    import webbrowser
    import threading
    threading.Timer(1.5, lambda: webbrowser.open(f"http://{args.host}:{bind_port}")).start()

    # Launch FastAPI Server
    uvicorn.run("web.server:app", host=args.host, port=bind_port, reload=False)


if __name__ == "__main__":
    main()
