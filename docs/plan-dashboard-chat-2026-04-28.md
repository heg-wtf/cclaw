# Plan: Dashboard Chat UI (Bidirectional with Telegram)
- date: 2026-04-28
- status: done
- author: claude
- approved-by:

## 1. 목적 및 배경

Abysscope 대시보드에서 각 봇과 직접 채팅할 수 있는 UI 추가.
- Telegram 세션을 그대로 이어서 이전 대화 맥락 유지
- 대시보드에서 보낸 메시지가 Telegram에도 나타남 (양방향)
- Telegram에서 온 메시지도 대시보드에 실시간 표시

## 2. 예상 임팩트

- **영향 모듈**: `bot_manager.py`, `handlers.py`, `session.py`, `config.py`, `abysscope/`
- **새 모듈**: `chat_server.py` (aiohttp HTTP/SSE 서버)
- **사용자 경험**: 브라우저에서 봇과 채팅 가능, Telegram과 완전 동기화

## 3. 구현 방법 비교

### Option A: Next.js가 Python 프로세스 직접 호출 (subprocess)
장점: 인프라 추가 없음  
단점: 실시간 스트리밍 불가, 프로세스 격리 문제, 세션 공유 불가

### Option B: abyss 프로세스에 내부 HTTP 서버 추가 ✅ 선택
장점: 기존 LLMBackend/세션/Telegram 인스턴스 직접 재사용. SSE 스트리밍 자연스러움.  
단점: abyss 프로세스에 HTTP 서버 추가 필요 (aiohttp, 이미 의존성 있음)

### Option C: Redis / message queue 경유
장점: 완전 분리  
단점: 과도한 인프라, 이 프로젝트 규모에 맞지 않음

**선택: Option B**. abyss 프로세스가 이미 asyncio event loop 위에서 동작하므로 aiohttp 서버를 같은 루프에 추가하는 것이 자연스럽다.

## 4. 구현 단계

### Phase 1: abyss 내부 HTTP 서버

- [ ] `src/abyss/chat_server.py` 신규 생성
  - `aiohttp.web` 기반 HTTP 서버 (포트 3849, 기본값)
  - `POST /bots/{name}/chat` — 메시지 전송, SSE 스트리밍 응답
  - `GET /bots/{name}/stream` — 새 메시지 SSE 구독 (Telegram + Dashboard 발신 모두)
  - `GET /bots/{name}/history` — 현재 세션 대화 히스토리 반환
  - 인증: `localhost` only (외부 노출 없음)

- [ ] `bot_manager.py`에 chat server 시작/종료 통합
  - `_run_bots()` 내 `aiohttp.web.AppRunner` 추가
  - graceful shutdown 시 chat server도 종료

- [ ] `bot.yaml` 스키마에 `primary_chat_id` 필드 추가
  - `handlers.py`에서 첫 DM 수신 시 `primary_chat_id` 자동 저장

### Phase 2: 세션 연속성

- [ ] `chat_server.py`에서 `primary_chat_id`가 있으면 해당 세션 디렉토리 재사용
  - `session_directory(bot_path, primary_chat_id)` 사용
  - `primary_chat_id` 없으면 `dashboard` 전용 세션 (`chat_dashboard`) 생성

- [ ] `LLMRequest` 생성 시 `session_key = f"{bot_name}:dashboard"` 사용
  - SDK pool이 Telegram 세션과 별도 클라이언트 유지 (충돌 방지)
  - `claude_session_id`는 primary_chat_id 세션에서 읽어서 `resume_session=True`

### Phase 3: Telegram 역동기화

- [ ] `chat_server.py`에서 메시지 처리 후 Bot API로 Telegram 전송
  - `primary_chat_id`가 있을 때만 동기화
  - 대시보드 발신 메시지: `[Dashboard] {message}` prefix
  - 봇 응답: 그대로 전송

- [ ] `handlers.py`에서 Telegram 메시지 수신 시 SSE 구독자에게 브로드캐스트
  - `ChatEventBus` 클래스: `asyncio.Queue` per bot, subscribe/publish
  - 유저 메시지 + 봇 응답 모두 이벤트 발행

### Phase 4: Abysscope Chat UI

- [ ] `abysscope/src/app/bots/[name]/chat/page.tsx` 신규 페이지
  - 메시지 리스트 (유저/봇 구분, 출처 표시: Telegram/Dashboard)
  - 입력창 + 전송 버튼
  - 스트리밍 응답 실시간 렌더링

- [ ] `abysscope/src/app/api/bots/[name]/chat/route.ts`
  - `POST` — abyss chat server `POST /bots/{name}/chat` 프록시
  - `GET` (SSE) — abyss chat server `GET /bots/{name}/stream` 프록시

- [ ] Sidebar에 각 봇의 "Chat" 링크 추가

## 5. 테스트 계획

**단위 테스트:**
- [ ] `ChatEventBus.publish()` → 구독자 수신 확인
- [ ] `primary_chat_id` 없을 때 dashboard 전용 세션 생성
- [ ] `primary_chat_id` 있을 때 기존 세션 디렉토리 재사용

**통합 테스트:**
- [ ] 대시보드 메시지 전송 → 봇 응답 SSE 수신 → Telegram 동기화 확인
- [ ] Telegram 메시지 → 대시보드 SSE 이벤트 수신 확인
- [ ] abyss 프로세스 재시작 후 세션 연속성 확인

## 6. 사이드 이펙트

- `bot_manager.py` 변경: asyncio event loop에 aiohttp runner 추가. 기존 Telegram polling과 동일 루프 공유 → 호환성 문제 없음 (python-telegram-bot도 asyncio 기반)
- `handlers.py` 변경: `primary_chat_id` 저장 로직 추가. 기존 핸들러 동작 변경 없음
- `bot.yaml` 스키마 변경: `primary_chat_id` 필드 추가. 없는 기존 파일은 그냥 None으로 처리, 하위 호환

## 7. 보안 검토

- chat server는 `127.0.0.1` (localhost) only bind. 외부 노출 없음
- Next.js → chat server 통신도 localhost only
- `primary_chat_id` 저장 시 정수 검증 (Telegram user ID 형식)
- 대시보드 발신 메시지도 `session.log_conversation()`으로 기록 → FTS5 인덱스에도 포함
- OWASP: XSS 없음 (React 자동 이스케이프), SQL injection 없음 (FTS5 파라미터 바인딩)

## 8. 포트 정책

| 서비스 | 포트 |
|--------|------|
| abysscope (Next.js) | 3847 |
| abyss chat server (aiohttp) | 3849 |
| QMD daemon | 8181 |

`ABYSS_CHAT_PORT` 환경변수로 오버라이드 가능.
