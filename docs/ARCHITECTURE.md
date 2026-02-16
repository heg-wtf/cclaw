# 아키텍처

## 전체 구조

```
Telegram ←→ python-telegram-bot (Long Polling) ←→ handlers.py ←→ claude_runner.py ←→ Claude Code CLI
                                                       ↕
                                                  session.py ←→ ~/.cclaw/bots/<name>/sessions/
```

## 핵심 설계 결정

### 1. Claude Code subprocess 위임

LLM API를 직접 호출하지 않고 `claude -p` CLI를 subprocess로 실행한다.

- Claude Code의 에이전트 능력(파일 조작, 코드 실행)을 그대로 활용
- API 키 관리 불필요 (Claude Code가 자체 인증 처리)
- subprocess의 `cwd` 파라미터로 세션 디렉토리를 작업 디렉토리로 설정
- `--model` 플래그로 모델 선택 (sonnet/opus/haiku)

### 2. 파일 기반 세션

DB 없이 디렉토리 구조로 세션을 관리한다.

- 각 채팅은 `chat_<id>/` 디렉토리
- `CLAUDE.md`: Claude Code가 읽는 시스템 프롬프트
- `conversation.md`: 대화 로그 (마크다운 append)
- `workspace/`: Claude Code가 생성하는 파일 저장소

### 3. 멀티봇 아키텍처

하나의 프로세스에서 여러 Telegram 봇을 동시 실행한다.

- 봇마다 독립된 `Application` 인스턴스
- `asyncio` 기반 동시 polling
- 봇별 독립 설정 (토큰, 성격, 역할, 권한, 모델)
- 개별 봇 오류가 다른 봇에 영향을 주지 않도록 격리

### 4. 세션별 동시성 제어

같은 채팅에서 동시에 여러 메시지가 오면 순차 처리한다.

- `{bot_name}:{chat_id}` 키로 `asyncio.Lock` 관리
- Lock이 잡혀있으면 "Message queued" 알림 후 대기 (메시지 큐잉)

### 5. 프로세스 추적

실행 중인 Claude Code subprocess를 세션별로 추적한다.

- `_running_processes` 딕셔너리에 `{bot_name}:{chat_id}` → `subprocess` 매핑
- `/cancel` 명령으로 실행 중인 프로세스를 SIGKILL로 중단
- `returncode == -9`이면 `asyncio.CancelledError` 발생

### 6. 모델 선택

봇별로 Claude 모델을 설정하고 런타임에 변경할 수 있다.

- `bot.yaml`의 `model` 필드에 저장 (기본값: sonnet)
- Telegram `/model` 커맨드로 런타임 변경 (변경 시 bot.yaml에 즉시 저장)
- CLI `cclaw bot model <name> <model>`로도 변경 가능
- 유효 모델: sonnet, opus, haiku

## 모듈 의존성

```
cli.py
├── onboarding.py → config.py
├── bot_manager.py
│   ├── config.py
│   ├── handlers.py
│   │   ├── claude_runner.py
│   │   ├── session.py
│   │   ├── config.py (save_bot_config, VALID_MODELS)
│   │   └── utils.py
│   └── utils.py
└── config.py
```

## 프로세스 관리

- **포그라운드**: `cclaw start` → `asyncio.run()` → Ctrl+C로 종료
- **데몬**: `cclaw start --daemon` → launchd plist 생성 → `launchctl load`
- **PID 파일**: `~/.cclaw/cclaw.pid`에 현재 프로세스 ID 기록
- **Graceful Shutdown**: SIGINT/SIGTERM 시그널 핸들러로 봇 순차 종료

## 메시지 처리 흐름

### 텍스트 메시지
```
수신 → 권한 체크 → 세션 Lock (큐잉) → ensure_session → typing 주기 전송(4초) → claude -p --model <model> → Markdown→HTML 변환 → 분할 전송
```

### 파일 (사진/문서)
```
수신 → 권한 체크 → 세션 Lock (큐잉) → workspace에 다운로드 → 캡션 + 파일경로를 Claude에 전달 → 응답 전송
```

### /cancel 명령
```
수신 → 권한 체크 → _running_processes에서 프로세스 조회 → process.kill() → "Execution cancelled" 응답
```

### /send 명령
```
수신 → 권한 체크 → workspace 파일 조회 → reply_document()로 전송
```
