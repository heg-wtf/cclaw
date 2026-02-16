# cclaw (claude-claw)

Telegram + Claude Code 기반 개인 AI 어시스턴트.
로컬 Mac(Intel/Apple Silicon)에서 실행되는 멀티봇, 파일 기반 세션 시스템.

## 설계 원칙

- **로컬 퍼스트**: 서버 없음. Long Polling. SSL/공인IP 불필요.
- **파일 기반**: DB 없음. 세션 = 디렉토리. 대화 = 마크다운.
- **Claude Code 위임**: LLM API 직접 호출 없음. `claude -p`를 subprocess로 실행.
- **CLI 퍼스트**: 온보딩부터 봇 관리까지 터미널에서 완결.

## 기술 스택

| 구분 | 선택 |
|------|------|
| 패키지 관리 | uv |
| CLI | Typer + Rich |
| Telegram | python-telegram-bot v21+ |
| 설정 | PyYAML |
| AI 엔진 | Claude Code CLI (`claude -p`) |
| 프로세스 관리 | launchd (macOS) |

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

## CLI 명령어

```bash
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

# 실행
cclaw start                    # 포그라운드
cclaw start --daemon           # 백그라운드 (launchd)
cclaw stop                     # 데몬 중지
cclaw status                   # 실행 상태

# 로그
cclaw logs                     # 오늘 로그 출력
cclaw logs -f                  # tail -f 모드
```

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
| `/cancel` | 실행 중인 프로세스 중단 |
| `/version` | 버전 정보 |
| `/help` | 명령어 목록 |

## 파일 처리

사진이나 문서를 봇에게 보내면 자동으로 workspace에 저장되고 Claude Code에게 전달됩니다.
캡션을 함께 보내면 캡션이 프롬프트로 사용됩니다.
`/send` 명령어로 workspace 파일을 텔레그램으로 다시 받을 수 있습니다.

## 프로젝트 구조

```
cclaw/
├── pyproject.toml
├── src/cclaw/
│   ├── cli.py              # Typer CLI 엔트리포인트
│   ├── config.py           # 설정 로드/저장
│   ├── onboarding.py       # 초기 설정 마법사
│   ├── claude_runner.py    # Claude Code subprocess 실행
│   ├── session.py          # 세션 디렉토리 관리
│   ├── handlers.py         # Telegram 핸들러 팩토리
│   ├── bot_manager.py      # 멀티봇 라이프사이클
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
│       └── sessions/
│           └── chat_<id>/
│               ├── CLAUDE.md
│               ├── conversation.md
│               └── workspace/
└── logs/
```

## 테스트

```bash
uv run pytest
# 또는
pytest
```

## 라이선스

MIT
