# 🏛️ AutoThreads AI 시스템 아키텍처 및 기술 명세서

본 문서는 **쓰레드 × 쿠팡파트너스 24시간 무인 자동화 시스템**의 소프트웨어 아키텍처, 데이터 흐름, 모듈 인터페이스 및 설계 원칙을 상세히 정의합니다.

---

## 1. 하이레벨 아키텍처 (High-Level Architecture)

```mermaid
graph TD
    A[Coupang Partners OpenAPI / Crawler] -->|1. 상품 소싱 & 필터링| B(Product Filter Engine)
    B -->|통과 상품 적재| DB[(SQLite: automation.db)]
    
    subgraph Core Automation Pipeline
        C[AutoPilot Scheduler: APScheduler] -->|골든타임 트리거| D[DeepLink Manager]
        D -->|HMAC-SHA256 딥링크 변환| E[LLM Copywriting Engine]
        E -->|본문 300자 + 3단계 댓글| F[Pillow Card News Renderer]
        F -->|1080x1080 슬라이드| G[Public CDN Image Uploader]
        G -->|공개 HTTPS URL| H[Meta Threads & Instagram API]
    end

    DB <--> Core Automation Pipeline
    H -->|실시간 발행| I[Threads / Instagram Live Feeds]
    H -->|결과 알림| J[Discord / Telegram Webhook]
    
    subgraph Web Control Panel
        K[FastAPI Backend Server] <--> DB
        L[Dark Glassmorphism Dashboard] <--> K
    end
```

---

## 2. 5단계 무인 자동화 파이프라인 명세

### [Step 1] 상품 소싱 및 필터 모듈 (`modules/sourcing/`)
* **목적:** 전환율이 가장 높은 4대 카테고리(생활용품, 아이디어, 펫, 다이어트)에서 고품질 상품을 자동 선별.
* **필터링 알고리즘:**
  $$\text{Pass} \iff (10,000 \le \text{Price} \le 39,900) \wedge (\text{Rating} \ge 4.5) \wedge (\text{Reviews} \ge 1,000) \wedge (\text{isRocket} = \text{True})$$
* **중복 방지:** `product_id` 고유 키로 SQLite에 기록하여 기발행 상품 중복 소싱 방지.

### [Step 2] 파트너스 딥링크 변환 모듈 (`modules/deeplink/`)
* **인증 방식:** 쿠팡 공식 HMAC-SHA256 시그니처 생성
  * Header: `Authorization: CEA algorithm=HmacSHA256, access-key={KEY}, signed-date={GMT}, signature={HEX}`
  * Endpoint: `POST /v2/providers/affiliate_open_api/apis/openapi/v1/deeplink`
* **API 미발급자 폴백(Fallback):** 쿠팡 가입 초기 OpenAPI 미발급자를 위한 `default_affiliate_link`(대표 링크/리틀리 링크) 자동 주입 지원.

### [Step 3] AI 카피라이팅 엔진 (`modules/writer/`)
* **본문 규칙 (섀도우밴 원천 방지):**
  * 길이: 300자 이내
  * 구조: 1문장 1줄(25자 내외), 2~3줄마다 공백 줄
  * 금지 사항: 본문 URL 금지, 홍보성 키워드 금지, 해시태그 금지, 기계적 어조 금지
  * 엔딩: 자연스러운 댓글 유도 문구
* **댓글 3단계 구조화:**
  * **댓글 1:** 공정위 필수 문구 + 제품/배송 요약 + 파트너스 링크
  * **댓글 2:** 실사용 디테일 꿀팁 + 파트너스 링크
  * **댓글 3:** 참여 유도 및 마무리

### [Step 4] 비주얼 카드뉴스 자동 렌더링 (`modules/visual/`)
* **엔진:** Pillow (PIL)
* **스펙:** 1080×1080 해상도, 다크 슬레이트 테마, 로켓배송/리뷰 뱃지, 유니코드 표준 기호 사용
* **CDN 업로더 (`uploader.py`):** 메타 Graph API가 로컬 이미지를 다운로드할 수 있도록 공개 HTTPS URL로 1초 내 즉시 업로드.

### [Step 5] 플랫폼 연동 & 스케줄러 (`modules/publisher/`, `modules/scheduler/`)
* **쓰레드 API:** 메타 공식 Threads Graph API (`https://graph.threads.net/v1.0`)
  * User ID 자동 리졸빙 지원 (`/me` 엔드포인트 연동)
  * 본문 컨테이너 생성 ➔ 발행 ➔ 20초 딜레이 ➔ 댓글 1~3 순차 답글 발행
* **안티봇 지터:** 골든타임 도달 시 `±15분` 무작위 지연(Jitter) 실행.
* **1:3 안티 스팸 비율:** 수익화 글 1개당 정보/공감 글 3개 자동 교차 발행.

---

## 3. 데이터베이스 스키마 (`data/automation.db`)

```sql
-- 상품 풀 테이블
CREATE TABLE products (
    product_id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    price INTEGER NOT NULL,
    rating REAL NOT NULL,
    review_count INTEGER NOT NULL,
    is_rocket INTEGER NOT NULL,
    category TEXT NOT NULL,
    original_url TEXT NOT NULL,
    image_url TEXT,
    deeplink TEXT,
    created_at TEXT NOT NULL,
    posted_at TEXT,
    status TEXT DEFAULT 'pending'
);

-- 포스트 발행 이력 테이블
CREATE TABLE posts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id TEXT,
    post_type TEXT DEFAULT 'affiliate',
    platform TEXT DEFAULT 'threads',
    main_text TEXT NOT NULL,
    comment_1 TEXT,
    comment_2 TEXT,
    comment_3 TEXT,
    image_paths TEXT,
    platform_post_id TEXT,
    status TEXT DEFAULT 'pending',
    scheduled_at TEXT,
    published_at TEXT,
    error_msg TEXT,
    FOREIGN KEY (product_id) REFERENCES products(product_id)
);

-- 시스템 감사 로그 테이블
CREATE TABLE logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    level TEXT NOT NULL,
    module TEXT NOT NULL,
    message TEXT NOT NULL
);
```
