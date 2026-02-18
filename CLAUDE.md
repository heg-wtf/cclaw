# cclaw 개발 가이드

## 프로젝트 개요

Telegram + Claude Code 기반 개인 AI 어시스턴트. 로컬 Mac에서 실행되는 CLI 도구.

## 기술 스택

- Python >= 3.11, uv 패키지 관리
- Typer (CLI), Rich (출력), python-telegram-bot v21+ (async), PyYAML (설정), croniter (cron 스케줄)
- Claude Code CLI를 subprocess로 실행 (`claude -p`)

## 주요 명령어

```bash
uv sync                      # 의존성 설치
uv run cclaw --help          # CLI 도움말
uv run cclaw doctor          # 환경 점검
uv run cclaw init            # 온보딩
uv run cclaw start           # 봇 실행
uv run cclaw bot list        # 봇 목록 (모델 표시)
uv run cclaw bot model <name>       # 현재 모델 확인
uv run cclaw bot model <name> opus  # 모델 변경
uv run cclaw skills                  # 전체 스킬 목록 (미연결 포함)
uv run cclaw skill add               # 대화형 스킬 생성
uv run cclaw skill setup <name>      # 스킬 셋업/활성화
uv run cclaw skill edit <name>       # SKILL.md 편집
uv run cclaw skill remove <name>     # 스킬 삭제
uv run cclaw skill test <name>       # 요구사항 테스트
uv run cclaw cron list <bot>         # cron job 목록
uv run cclaw cron add <bot>          # 대화형 cron job 생성
uv run cclaw cron remove <bot> <job> # cron job 삭제
uv run cclaw cron enable <bot> <job> # cron job 활성화
uv run cclaw cron disable <bot> <job> # cron job 비활성화
uv run cclaw cron run <bot> <job>    # cron job 즉시 실행 (테스트용)
uv run cclaw heartbeat status        # 봇별 heartbeat 상태 표시
uv run cclaw heartbeat enable <bot>  # heartbeat 활성화
uv run cclaw heartbeat disable <bot> # heartbeat 비활성화
uv run cclaw heartbeat run <bot>     # heartbeat 즉시 실행 (테스트용)
uv run cclaw heartbeat edit <bot>    # HEARTBEAT.md 편집
uv run cclaw logs            # 오늘 로그 출력
uv run cclaw logs -f         # tail -f 모드
uv run pytest                # 테스트
uv run pytest -v             # 테스트 (상세)
uv run pytest tests/test_config.py  # 개별 테스트

# pip/pipx 설치 시에는 uv run 없이 직접 실행
cclaw --help
cclaw start
pytest
```

## 코드 구조

- `src/cclaw/cli.py` - Typer 앱 엔트리포인트, 모든 커맨드 정의 (skills, bot, skill, cron, heartbeat 서브커맨드 포함)
- `src/cclaw/config.py` - `~/.cclaw/` 설정 관리 (YAML)
- `src/cclaw/onboarding.py` - 환경 점검, 토큰 검증, 봇 생성 마법사
- `src/cclaw/claude_runner.py` - `claude -p` subprocess 실행 (async, `shutil.which`로 경로 해석, 프로세스 추적, 모델 선택, 스킬 MCP/env 주입, streaming 출력 지원)
- `src/cclaw/session.py` - 세션 디렉토리/대화 로그/workspace 관리
- `src/cclaw/handlers.py` - Telegram 핸들러 팩토리 (슬래시 커맨드 + 메시지 + 파일 수신/전송 + 모델 변경 + 프로세스 취소 + /skills 전체 목록 + /skill 관리 + /cron 관리 + /heartbeat 관리 + 스트리밍 응답)
- `src/cclaw/bot_manager.py` - 멀티봇 polling, launchd 데몬, 개별 봇 오류 격리, cron/heartbeat 스케줄러 통합
- `src/cclaw/heartbeat.py` - Heartbeat 주기적 상황 인지 (설정 CRUD, active hours 체크, HEARTBEAT.md 관리, HEARTBEAT_OK 감지, 스케줄러 루프)
- `src/cclaw/cron.py` - Cron 스케줄 자동화 (cron.yaml CRUD, croniter 기반 스케줄 매칭, one-shot 지원, 스케줄러 루프)
- `src/cclaw/skill.py` - 스킬 관리 (인식/로딩/생성/삭제, 봇-스킬 연결, CLAUDE.md 조합, MCP/환경변수 병합)
- `src/cclaw/utils.py` - 메시지 분할, Markdown→HTML 변환, 로깅 설정

## 코드 스타일

- 약어 사용 지양. 전체 full text 사용 (예: `session_directory`, `bot_config` 등)
- 타입 힌트 사용 (`from __future__ import annotations`)
- async/await 패턴 (Telegram, Claude Runner)
- `CCLAW_HOME` 환경변수로 테스트 시 경로 오버라이드 가능
- 모든 경로는 절대경로 사용. `config.py`의 `bot_directory(name)` 등 헬퍼 함수를 통해 접근. `pathlib.Path` 사용 권장

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

## 스트리밍 응답

- `run_claude_streaming()`으로 `--output-format stream-json --verbose --include-partial-messages` 실행
- `on_text_chunk` 콜백으로 토큰 단위 텍스트 수신
- Telegram 메시지를 실시간 편집하여 스트리밍 효과 구현 (커서: `▌`)
- 스로틀링: 0.5초 간격으로 메시지 편집 (`STREAM_THROTTLE_SECONDS`)
- 최소 10자 이상 누적 후 첫 메시지 전송 (`STREAM_MIN_CHARS_BEFORE_SEND`)
- 4096자 초과 시 스트리밍 미리보기 중단, 최종 응답을 분할 전송
- typing 액션 대신 실시간 메시지 편집으로 대체

## 런타임 데이터 구조

```
~/.cclaw/
├── config.yaml           # 전역 설정 (봇 목록, log_level, command_timeout)
├── cclaw.pid             # 실행 중 PID
├── bots/<name>/
│   ├── bot.yaml          # 봇 설정 (토큰, 성격, 역할, allowed_users, model, skills, heartbeat)
│   ├── CLAUDE.md         # 봇 시스템 프롬프트 (스킬 내용 포함)
│   ├── cron.yaml         # Cron job 설정 (schedule/at, message, skills, model)
│   ├── cron_sessions/<job_name>/  # Cron job별 작업 디렉토리
│   │   └── CLAUDE.md     # 봇 CLAUDE.md 복사본
│   ├── heartbeat_sessions/       # Heartbeat 전용 작업 디렉토리
│   │   ├── CLAUDE.md     # 봇 CLAUDE.md 복사본
│   │   ├── HEARTBEAT.md  # 체크리스트 (사용자 편집 가능)
│   │   └── workspace/    # 파일 저장소
│   └── sessions/chat_<id>/
│       ├── CLAUDE.md     # 세션별 컨텍스트
│       ├── conversation.md  # 대화 로그
│       └── workspace/    # 파일 저장소
├── skills/<name>/
│   ├── SKILL.md          # 스킬 지시사항 (필수, 봇 CLAUDE.md에 합성됨)
│   ├── skill.yaml        # 스킬 설정 (도구 기반 스킬만: type, status, required_commands, environment_variables)
│   └── mcp.json          # MCP 서버 설정 (MCP 스킬만: mcpServers)
└── logs/                 # 일별 로테이션 로그
```
