# cclaw 개발 가이드

## 프로젝트 개요

Telegram + Claude Code 기반 개인 AI 어시스턴트. 로컬 Mac에서 실행되는 CLI 도구.

## 기술 스택

- Python >= 3.11, uv 패키지 관리
- Typer (CLI), Rich (출력), python-telegram-bot v21+ (async), PyYAML (설정)
- Claude Code CLI를 subprocess로 실행 (`claude -p`)

## 주요 명령어

```bash
uv sync                      # 의존성 설치
uv run cclaw --help          # CLI 도움말
uv run cclaw doctor          # 환경 점검
uv run cclaw init            # 온보딩
uv run cclaw start           # 봇 실행
uv run pytest                # 테스트
uv run pytest -v             # 테스트 (상세)
uv run pytest tests/test_config.py  # 개별 테스트
```

## 코드 구조

- `src/cclaw/cli.py` - Typer 앱 엔트리포인트, 모든 커맨드 정의
- `src/cclaw/config.py` - `~/.cclaw/` 설정 관리 (YAML)
- `src/cclaw/onboarding.py` - 환경 점검, 토큰 검증, 봇 생성 마법사
- `src/cclaw/claude_runner.py` - `claude -p` subprocess 실행 (async)
- `src/cclaw/session.py` - 세션 디렉토리/대화 로그/workspace 관리
- `src/cclaw/handlers.py` - Telegram 핸들러 팩토리 (슬래시 커맨드 + 메시지 + 파일 수신)
- `src/cclaw/bot_manager.py` - 멀티봇 polling, launchd 데몬
- `src/cclaw/utils.py` - 메시지 분할, Markdown→HTML 변환, 로깅 설정

## 코드 스타일

- 약어 사용 지양. 전체 full text 사용 (예: `session_directory`, `bot_config` 등)
- 타입 힌트 사용 (`from __future__ import annotations`)
- async/await 패턴 (Telegram, Claude Runner)
- `CCLAW_HOME` 환경변수로 테스트 시 경로 오버라이드 가능

## 테스트 규칙

- 모든 모듈에 대응하는 테스트 파일 존재 (`tests/test_*.py`)
- Telegram API 호출은 mock 처리
- `tmp_path` + `monkeypatch`로 파일시스템 격리
- `pytest-asyncio`로 async 테스트

## Telegram 메시지 포맷팅

- Claude 응답의 Markdown은 `utils.markdown_to_telegram_html()`로 HTML 변환 후 전송
- 변환 대상: `**bold**`, `*italic*`, `` `code` ``, ` ```code blocks``` `, `## headings`, `[link](url)`
- HTML 전송 실패 시 plain text 폴백
- 4096자 초과 시 `split_message()`로 자동 분할

## 런타임 데이터 구조

```
~/.cclaw/
├── config.yaml           # 전역 설정 (봇 목록, log_level, command_timeout)
├── cclaw.pid             # 실행 중 PID
├── bots/<name>/
│   ├── bot.yaml          # 봇 설정 (토큰, 성격, 역할, allowed_users)
│   ├── CLAUDE.md         # 봇 시스템 프롬프트
│   └── sessions/chat_<id>/
│       ├── CLAUDE.md     # 세션별 컨텍스트
│       ├── conversation.md  # 대화 로그
│       └── workspace/    # 파일 저장소
└── logs/                 # 일별 로테이션 로그
```
