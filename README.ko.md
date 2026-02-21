```
  ██████╗ ██████╗██╗      █████╗ ██╗    ██╗
 ██╔════╝██╔════╝██║     ██╔══██╗██║    ██║
 ██║     ██║     ██║     ███████║██║ █╗ ██║
 ██║     ██║     ██║     ██╔══██║██║███╗██║
 ╚██████╗╚██████╗███████╗██║  ██║╚███╔███╔╝
  ╚═════╝ ╚═════╝╚══════╝╚═╝  ╚═╝ ╚══╝╚══╝
```

# cclaw (claude-claw)

> [English](README.md)

Telegram + Claude Code 기반 개인 AI 어시스턴트.
로컬 Mac(Intel/Apple Silicon)에서 실행되는 멀티봇, 파일 기반 세션 시스템.

## 목차

- [설계 원칙](#설계-원칙)
- [요구사항](#요구사항)
- [설치](#설치)
- [사용법](#사용법)
- [스킬](#스킬)
  - [💬 iMessage](#-imessage)
  - [⏰ Apple Reminders](#-apple-reminders)
- [Telegram 명령어](#telegram-명령어)
- [파일 처리](#파일-처리)
- [기술 스택](#기술-스택)
- [CLI 명령어](#cli-명령어)
- [프로젝트 구조](#프로젝트-구조)
- [런타임 데이터](#런타임-데이터)
- [문서](#문서)
- [테스트](#테스트)
- [라이선스](#라이선스)

## 설계 원칙

- **로컬 퍼스트**: 서버 없음. Long Polling. SSL/공인IP 불필요.
- **파일 기반**: DB 없음. 세션 = 디렉토리. 대화 = 마크다운.
- **Claude Code 위임**: LLM API 직접 호출 없음. `claude -p`를 subprocess로 실행.
- **CLI 퍼스트**: 온보딩부터 봇 관리까지 터미널에서 완결.

## 요구사항

- Python >= 3.11
- Node.js (Claude Code 런타임)
- [Claude Code CLI](https://www.npmjs.com/package/@anthropic-ai/claude-code)
- [uv](https://docs.astral.sh/uv/)

## 설치

### uv (권장)

```bash
uv sync
```

### pip / pipx

```bash
pip install .
# 또는
pipx install .
```

## 사용법

```bash
# 환경 점검
cclaw doctor                    # pip/pipx 설치 시
uv run cclaw doctor             # uv 사용 시

# 최초 설정 (Telegram 봇 토큰 필요)
cclaw init

# 봇 관리
cclaw bot list
cclaw bot add
cclaw bot remove <name>

# 봇 실행
cclaw start              # 포그라운드
cclaw start --daemon     # 백그라운드 (launchd)
cclaw stop               # 데몬 중지
cclaw status             # 실행 상태 확인
```

## 스킬

cclaw는 봇의 기능을 도구와 지식으로 확장하는 **스킬 시스템**을 제공합니다. 스킬은 모듈식으로, 봇별로 자유롭게 연결/해제할 수 있습니다.

- **마크다운 스킬**: `SKILL.md` 파일 하나로 봇에 지시/지식을 추가합니다.
- **도구 기반 스킬**: `skill.yaml`에 CLI 도구, MCP 서버, 브라우저 자동화를 정의합니다.
- **빌트인 스킬**: 패키지에 포함된 스킬 템플릿을 `cclaw skills install <name>`으로 설치합니다.

### 💬 iMessage

[imsg](https://github.com/steipete/imsg) CLI를 사용하여 Telegram 봇으로 iMessage/SMS를 읽고 보낼 수 있습니다.

```bash
cclaw skills install imessage
cclaw skills setup imessage
```

Telegram에서:
```
/skills attach imessage
최근 메시지 목록 보여줘
임영선한테 "안녕" 보내줘
```

자세한 가이드: [iMessage 스킬 가이드](docs/skills/IMESSAGE.md)

### ⏰ Apple Reminders

[reminders-cli](https://github.com/keith/reminders-cli)를 사용하여 Telegram 봇으로 macOS 미리알림을 관리할 수 있습니다.

```bash
brew install keith/formulae/reminders-cli
cclaw skills install reminders
cclaw skills setup reminders
```

Telegram에서:
```
/skills attach reminders
오늘 할 일 보여줘
"장보기" 쇼핑 리스트에 내일까지 추가해줘
```

자세한 가이드: [Apple Reminders 스킬 가이드](docs/skills/REMINDERS.md)

## Telegram 명령어

| 명령어 | 설명 |
|--------|------|
| `/start` | 봇 소개 |
| `/reset` | 대화 초기화 (workspace 유지) |
| `/resetall` | 세션 전체 삭제 |
| `/files` | workspace 파일 목록 |
| `/send <filename>` | workspace 파일 전송 |
| `/status` | 세션 상태 |
| `/model` | 현재 모델 표시 |
| `/model <name>` | 모델 변경 (sonnet/opus/haiku) |
| `/streaming` | 스트리밍 상태 표시 |
| `/streaming on/off` | 스트리밍 모드 전환 |
| `/skills` | 전체 스킬 목록 (설치된 + 빌트인 미설치) |
| `/skills attach <name>` | 스킬 연결 |
| `/skills detach <name>` | 스킬 해제 |
| `/cron list` | cron job 목록 |
| `/cron run <name>` | cron job 즉시 실행 |
| `/heartbeat` | heartbeat 상태 |
| `/heartbeat on` | heartbeat 활성화 |
| `/heartbeat off` | heartbeat 비활성화 |
| `/heartbeat run` | heartbeat 즉시 실행 |
| `/cancel` | 실행 중인 프로세스 중단 |
| `/version` | 버전 정보 |
| `/help` | 명령어 목록 |

## 파일 처리

사진이나 문서를 봇에게 보내면 자동으로 workspace에 저장되고 Claude Code에게 전달됩니다.
캡션을 함께 보내면 캡션이 프롬프트로 사용됩니다.
`/send` 명령어로 workspace 파일을 텔레그램으로 다시 받을 수 있습니다.

---

## 기술 스택

| 구분 | 선택 |
|------|------|
| 패키지 관리 | uv |
| CLI | Typer + Rich |
| Telegram | python-telegram-bot v21+ |
| 설정 | PyYAML |
| Cron 스케줄러 | croniter |
| AI 엔진 | Claude Code CLI (`claude -p`, 스트리밍) |
| 프로세스 관리 | launchd (macOS) |

## CLI 명령어

```bash
# 배너
cclaw                          # ASCII 아트 배너 표시

# 온보딩/점검
cclaw init                     # 최초 설정
cclaw doctor                   # 환경 점검

# 봇 관리
cclaw bot list                 # 봇 목록 (모델 표시)
cclaw bot add                  # 봇 추가
cclaw bot remove <name>        # 봇 삭제
cclaw bot edit <name>          # bot.yaml 편집
cclaw bot model <name>         # 현재 모델 확인
cclaw bot model <name> opus    # 모델 변경
cclaw bot streaming <name>     # 스트리밍 상태 확인
cclaw bot streaming <name> off # 스트리밍 on/off 전환

# 스킬 관리
cclaw skills                   # 전체 스킬 목록 (설치된 + 빌트인 미설치)
cclaw skills add               # 대화형 스킬 생성
cclaw skills remove <name>     # 스킬 삭제
cclaw skills setup <name>      # 스킬 셋업 (요구사항 확인 → 활성화)
cclaw skills test <name>       # 스킬 요구사항 테스트
cclaw skills edit <name>       # SKILL.md 편집 ($EDITOR)
cclaw skills builtins          # 빌트인 스킬 목록
cclaw skills install           # 빌트인 스킬 목록 (builtins와 동일)
cclaw skills install <name>    # 빌트인 스킬 설치

# Cron job 관리
cclaw cron list <bot>          # cron job 목록
cclaw cron add <bot>           # 대화형 cron job 생성
cclaw cron remove <bot> <job>  # cron job 삭제
cclaw cron enable <bot> <job>  # cron job 활성화
cclaw cron disable <bot> <job> # cron job 비활성화
cclaw cron run <bot> <job>     # cron job 즉시 실행 (테스트용)

# Heartbeat 관리
cclaw heartbeat status         # 봇별 heartbeat 상태 표시
cclaw heartbeat enable <bot>   # heartbeat 활성화
cclaw heartbeat disable <bot>  # heartbeat 비활성화
cclaw heartbeat run <bot>      # heartbeat 즉시 실행 (테스트용)
cclaw heartbeat edit <bot>     # HEARTBEAT.md 편집 ($EDITOR)

# 실행
cclaw start                    # 포그라운드
cclaw start --daemon           # 백그라운드 (launchd)
cclaw stop                     # 데몬 중지
cclaw status                   # 실행 상태

# 로그
cclaw logs                     # 오늘 로그 출력
cclaw logs -f                  # tail -f 모드
```

## 프로젝트 구조

```
cclaw/
├── pyproject.toml
├── src/cclaw/
│   ├── cli.py              # Typer CLI 엔트리포인트 (ASCII 아트 배너)
│   ├── config.py           # 설정 로드/저장
│   ├── onboarding.py       # 초기 설정 마법사
│   ├── claude_runner.py    # Claude Code subprocess 실행 (일반 + 스트리밍)
│   ├── session.py          # 세션 디렉토리 관리
│   ├── handlers.py         # Telegram 핸들러 팩토리
│   ├── bot_manager.py      # 멀티봇 라이프사이클
│   ├── skill.py            # 스킬 관리 (생성/연결/MCP/CLAUDE.md 조합)
│   ├── builtin_skills/     # 빌트인 스킬 템플릿 (imessage, reminders, ...)
│   │   ├── __init__.py     # 빌트인 스킬 레지스트리
│   │   ├── imessage/       # iMessage 스킬 (imsg CLI)
│   │   └── reminders/      # Apple Reminders 스킬 (reminders-cli)
│   ├── cron.py             # Cron 스케줄 자동화
│   ├── heartbeat.py        # Heartbeat (주기적 상황 인지)
│   └── utils.py            # 유틸리티
└── tests/
```

## 런타임 데이터

`~/.cclaw/` 디렉토리에 설정과 세션 데이터가 저장됩니다. `CCLAW_HOME` 환경변수로 경로를 변경할 수 있습니다.

```
~/.cclaw/
├── config.yaml
├── bots/
│   └── <bot-name>/
│       ├── bot.yaml
│       ├── CLAUDE.md
│       ├── cron.yaml             # Cron job 설정 (선택)
│       ├── cron_sessions/        # Cron job별 작업 디렉토리
│       ├── heartbeat_sessions/   # Heartbeat 전용 작업 디렉토리
│       │   ├── CLAUDE.md
│       │   ├── HEARTBEAT.md      # 체크리스트 (사용자 편집 가능)
│       │   └── workspace/
│       └── sessions/
│           └── chat_<id>/
│               ├── CLAUDE.md
│               ├── conversation.md
│               ├── .claude_session_id  # Claude Code 세션 ID (--resume용)
│               └── workspace/
├── skills/
│   └── <skill-name>/
│       ├── SKILL.md          # 스킬 지시사항 (필수)
│       ├── skill.yaml        # 스킬 설정 (도구 기반 스킬만)
│       └── mcp.json          # MCP 서버 설정 (MCP 스킬만)
└── logs/
```

## 문서

- [아키텍처](docs/ARCHITECTURE.md)
- [기술 노트](docs/TECHNICAL-NOTES.md)
- [iMessage 스킬 가이드](docs/skills/IMESSAGE.md)
- [Apple Reminders 스킬 가이드](docs/skills/REMINDERS.md)

## 테스트

```bash
uv run pytest
# 또는
pytest
```

## 라이선스

MIT
