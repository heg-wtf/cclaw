# cclaw (claude-claw)

Telegram + Claude Code 기반 개인 AI 어시스턴트.
로컬 Mac(Intel/Apple Silicon)에서 실행. 멀티봇. 파일 기반 세션.

---

## 설계 원칙

- **로컬 퍼스트**: 서버 없음. Long Polling. SSL/공인IP 불필요.
- **파일 기반**: DB 없음. 세션 = 디렉토리. 대화 = 마크다운. Git 친화적.
- **Claude Code 위임**: LLM API 직접 호출 없음. `claude -p`를 subprocess로 실행.
- **CLI 퍼스트**: Typer 기반 CLI. 온보딩부터 봇 관리까지 터미널에서 완결.
- **uv 기반**: pip/venv 대신 uv로 의존성 관리 및 실행.

---

## 기술 스택

| 구분 | 선택 | 이유 |
|------|------|------|
| 패키지 관리 | uv | 빠른 설치, lockfile, Python 버전 관리 통합 |
| CLI 프레임워크 | Typer | type hint 기반, 자동 --help, rich 출력 |
| Telegram | python-telegram-bot v21+ | async 네이티브, 활발한 유지보수 |
| 설정 | PyYAML | 사람이 읽고 편집하기 쉬움 |
| 콘솔 출력 | Rich | 온보딩 UI, 테이블, 프로그레스바 |
| AI 엔진 | Claude Code CLI | 에이전트 능력(코드 실행, 파일 조작) 내장 |
| 프로세스 관리 | launchd | macOS 네이티브, 자동 재시작 |

---

## 디렉토리 구조

### 프로젝트 소스

```
cclaw/
├── pyproject.toml
├── uv.lock
├── README.md
├── PLAN.md
├── CLAUDE.md
├── src/
│   └── cclaw/
│       ├── __init__.py
│       ├── cli.py                 # Typer 앱 (엔트리포인트)
│       ├── onboarding.py          # 초기 설정 마법사
│       ├── bot_manager.py         # 멀티봇 라이프사이클
│       ├── session.py             # 세션 디렉토리 관리
│       ├── claude_runner.py       # Claude Code subprocess 실행
│       ├── handlers.py            # Telegram 핸들러 팩토리
│       ├── config.py              # 설정 로드/저장
│       └── utils.py               # 메시지 분할, 로깅 등
└── tests/
    ├── test_session.py
    ├── test_claude_runner.py
    └── test_handlers.py
```

### 런타임 데이터 (~/.cclaw/)

```
~/.cclaw/
├── config.yaml                    # 전역 설정
├── bots/
│   ├── infra-bot/
│   │   ├── bot.yaml              # 봇 설정 (토큰, 성격, 역할)
│   │   ├── CLAUDE.md             # 봇 시스템 프롬프트 (자동생성)
│   │   └── sessions/
│   │       └── chat_{id}/
│   │           ├── CLAUDE.md     # 세션 컨텍스트
│   │           ├── conversation.md
│   │           └── workspace/
│   └── code-bot/
│       ├── bot.yaml
│       ├── CLAUDE.md
│       └── sessions/
└── logs/
    └── cclaw-250215.log           # cclaw-yymmdd.log (일별 로테이션)
```

---

## pyproject.toml

```toml
[project]
name = "cclaw"
version = "0.1.0"
description = "Telegram + Claude Code personal AI assistant"
requires-python = ">=3.11"
dependencies = [
    "python-telegram-bot>=21.0",
    "typer>=0.12.0",
    "pyyaml>=6.0",
    "rich>=13.0",
]

[project.scripts]
cclaw = "cclaw.cli:app"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/cclaw"]
```

---

## CLI 명령어 설계

```
cclaw init                         # 온보딩 (최초 1회)
cclaw bot add                      # 새 봇 추가
cclaw bot list                     # 봇 목록
cclaw bot remove <name>            # 봇 삭제
cclaw bot edit <name>              # 봇 설정 편집
cclaw start                        # 모든 봇 시작 (포그라운드)
cclaw start --bot <name>           # 특정 봇만 시작
cclaw start --daemon               # 백그라운드 실행
cclaw stop                         # 데몬 중지
cclaw status                       # 실행 상태
cclaw logs                         # 로그 tail -f
cclaw doctor                       # 환경 점검
```

### Typer 구조

```python
# src/cclaw/cli.py
import typer

app = typer.Typer(help="cclaw - Telegram + Claude Code AI assistant")
bot_app = typer.Typer(help="봇 관리")
app.add_typer(bot_app, name="bot")

@app.command()
def init():
    """최초 설정 마법사"""

@app.command()
def start(bot: str = None, daemon: bool = False):
    """봇 실행"""

@app.command()
def stop():
    """데몬 중지"""

@app.command()
def status():
    """실행 상태 확인"""

@app.command()
def logs():
    """로그 실시간 출력"""

@app.command()
def doctor():
    """환경 점검"""

@bot_app.command("add")
def bot_add():
    """새 봇 추가"""

@bot_app.command("list")
def bot_list():
    """봇 목록"""

@bot_app.command("remove")
def bot_remove(name: str):
    """봇 삭제"""

@bot_app.command("edit")
def bot_edit(name: str):
    """봇 설정 편집"""
```

---

## 온보딩 플로우 (`cclaw init`)

### Step 1: 사전 점검

```
$ cclaw init

🦀 cclaw 초기 설정을 시작합니다.

환경 점검 중...
  ✅ Python 3.12.3
  ✅ Node.js v20.11.0
  ✅ Claude Code v1.0.23 (/usr/local/bin/claude)
```

점검 항목:
- `shutil.which("claude")` → Claude Code 존재 확인
- `claude --version` → 버전 출력
- `shutil.which("node")` → Node.js 확인
- **Claude Code 미설치 시 안내 메시지 출력 후 즉시 종료**

```
  ❌ Claude Code가 설치되어 있지 않습니다.

  설치 방법:
    npm install -g @anthropic-ai/claude-code

  설치 후 다시 실행하세요: cclaw init
```

### Step 2: 텔레그램 봇 토큰 입력

```
✅ 환경 점검 완료!

📱 텔레그램 봇을 연결합니다.

  1. 텔레그램에서 @BotFather 에게 DM을 보내세요.
  2. /newbot 명령으로 봇을 만드세요.
  3. 발급받은 토큰을 아래에 입력하세요.

Bot Token: 123456789:ABCdefGHIjklMNOpqrsTUVwxyz

🔍 토큰 확인 중...
✅ 봇 확인됨: @my_infra_bot (My Infra Bot)
```

동작:
- `typer.prompt("Bot Token")` 으로 입력
- `telegram.Bot(token).get_me()` 호출하여 유효성 검증
- 성공 시 봇 이름/username 표시
- 실패 시 재입력 요청 (최대 3회)

### Step 3: 봇 프로필 생성

```
🤖 봇 프로필을 설정합니다.

봇 이름 (영문, 디렉토리명으로 사용): infra-bot
봇 성격: 꼼꼼하고 신중한 시니어 SRE. 명령 실행 전 항상 확인을 구한다.
하는 일: AWS 인프라 관리, K8s 배포, 모니터링 알림 분석

📝 생성 중...

  ╭─────────────────────────────────╮
  │  ✅ infra-bot 생성 완료!        │
  │                                 │
  │  이름:     infra-bot            │
  │  성격:     꼼꼼하고 신중한 ...   │
  │  하는 일:  AWS 인프라 관리 ...   │
  │  경로:     ~/.cclaw/bots/infra-bot/  │
  │  텔레그램: @my_infra_bot        │
  ╰─────────────────────────────────╯

  봇을 시작하려면: cclaw start
```

입력 항목:
- **이름**: 영문 slug. 디렉토리명. 중복 검사. 필수.
- **성격**: 자유 텍스트. CLAUDE.md 페르소나 섹션. 필수.
- **하는 일**: 자유 텍스트. CLAUDE.md 역할 섹션. 필수.

### 자동 생성 파일

**~/.cclaw/config.yaml**:
```yaml
bots:
  - name: infra-bot
    path: bots/infra-bot

settings:
  log_level: INFO
  command_timeout: 300
```

**~/.cclaw/bots/infra-bot/bot.yaml**:
```yaml
telegram_token: "123456789:ABCdefGHIjklMNOpqrsTUVwxyz"
telegram_username: "@my_infra_bot"
telegram_botname: "My Infra Bot"
description: "AWS 인프라 관리, K8s 배포, 모니터링 알림 분석"
personality: "꼼꼼하고 신중한 시니어 SRE. 명령 실행 전 항상 확인을 구한다."
allowed_users: []
claude_args: []
```

**~/.cclaw/bots/infra-bot/CLAUDE.md** (자동생성):
```markdown
# infra-bot

## 성격
꼼꼼하고 신중한 시니어 SRE. 명령 실행 전 항상 확인을 구한다.

## 역할
AWS 인프라 관리, K8s 배포, 모니터링 알림 분석

## 규칙
- 한국어로 응답한다.
- 파일을 생성할 때는 workspace/ 디렉토리에 저장한다.
- 위험한 명령(삭제, 재시작 등) 실행 전 반드시 확인을 구한다.
```

---

## Telegram Slash Command

| 커맨드 | 인자 | 동작 |
|--------|------|------|
| `/start` | - | 봇 소개 (이름, 성격, 하는 일) |
| `/reset` | - | conversation.md 삭제 (workspace 유지) |
| `/resetall` | - | 세션 디렉토리 전체 삭제 |
| `/files` | - | workspace 파일 목록 |
| `/send` | `{filename}` | workspace 파일 → 텔레그램 전송 |
| `/status` | - | 세션 상태, 대화 로그 크기 |
| `/cancel` | - | 실행 중인 Claude Code 종료 |
| `/help` | - | 명령어 목록 |

### /reset vs /resetall

| 커맨드 | conversation.md | CLAUDE.md | workspace/ |
|--------|:-:|:-:|:-:|
| `/reset` | 삭제 | 유지 | 유지 |
| `/resetall` | 삭제 | 삭제 | 삭제 |

---

## 구현 Phase

### Phase 1: 프로젝트 셋업 + 온보딩

`cclaw init`으로 봇을 설정할 수 있는 상태까지.

**Task 1.1: uv 프로젝트 초기화**
- [ ] pyproject.toml 작성
- [ ] src layout 구성 (`src/cclaw/__init__.py`)
- [ ] `uv sync` 로 의존성 설치
- [ ] `uv run cclaw --help` 동작 확인

**Task 1.2: CLI 뼈대 (`src/cclaw/cli.py`)**
- [ ] Typer 앱 생성
- [ ] bot 서브커맨드 그룹 등록
- [ ] 각 커맨드 placeholder 구현 (print만)
- [ ] `uv run cclaw --help` 확인
- [ ] `uv run cclaw bot --help` 확인

**Task 1.3: 설정 모듈 (`src/cclaw/config.py`)**
- [ ] `CCLAW_HOME` = `~/.cclaw/` (환경변수 `CCLAW_HOME`으로 오버라이드 가능)
- [ ] `load_config()` → config.yaml 로드, 없으면 None
- [ ] `save_config()` → config.yaml 저장
- [ ] `load_bot_config(name)` → bot.yaml 로드
- [ ] `save_bot_config(name, data)` → bot.yaml + CLAUDE.md 생성
- [ ] CLAUDE.md 템플릿 생성 함수

**Task 1.4: 온보딩 (`src/cclaw/onboarding.py`)**
- [ ] `run_onboarding()` 함수 구조
- [ ] Step 1: `shutil.which("claude")` Claude Code 존재 확인
- [ ] Step 1: `shutil.which("node")` Node.js 확인
- [ ] Step 1: 버전 출력, 미설치 시 안내 + `typer.Exit(1)`
- [ ] Step 2: `typer.prompt("Bot Token")` 입력
- [ ] Step 2: `telegram.Bot(token).get_me()` 토큰 검증
- [ ] Step 2: 실패 시 재입력 (최대 3회)
- [ ] Step 3: 봇 이름 입력 (영문 slug, 중복 검사)
- [ ] Step 3: 봇 성격 입력
- [ ] Step 3: 하는 일 입력
- [ ] Step 3: `~/.cclaw/` 디렉토리 구조 생성
- [ ] Step 3: config.yaml, bot.yaml, CLAUDE.md 자동 생성
- [ ] Rich Panel로 결과 표시

**Task 1.5: `cclaw doctor`**
- [ ] 사전 점검 로직 재사용 (Python, Node, Claude Code)
- [ ] config.yaml 존재 확인
- [ ] 봇별 토큰 유효성 검사
- [ ] 봇별 세션 수 카운트
- [ ] Rich 포맷 출력

**Task 1.6: `cclaw bot add / list / remove`**
- [ ] `bot add`: 온보딩 Step 2 + Step 3 재사용
- [ ] `bot list`: Rich Table로 봇 목록 출력
- [ ] `bot remove`: 확인 프롬프트 후 봇 디렉토리 삭제
- [ ] `bot remove`: config.yaml에서 항목 제거

### Phase 2: 코어 엔진 + 데몬

`cclaw start`로 텔레그램에서 Claude Code와 대화할 수 있고,
`cclaw start --daemon`으로 항상 실행 상태를 유지할 수 있는 상태까지.

**Task 2.1: Claude Runner (`src/cclaw/claude_runner.py`)**
- [ ] `async run_claude(cwd, message, extra_args, timeout) → str`
- [ ] `asyncio.create_subprocess_exec`로 `claude -p` 실행
- [ ] `--output-format text`, `--cwd` 옵션 설정
- [ ] `bot.yaml`의 `claude_args` 병합
- [ ] `asyncio.wait_for`로 타임아웃 처리
- [ ] stderr 캡처, returncode 체크
- [ ] 터미널에서 직접 실행하여 응답 확인 테스트

**Task 2.2: 세션 관리 (`src/cclaw/session.py`)**
- [ ] `ensure_session(bot_path, chat_id)` → 디렉토리 생성, 봇 CLAUDE.md 복사
- [ ] `reset_session(bot_path, chat_id)` → conversation.md 삭제 (workspace 유지)
- [ ] `reset_all_session(bot_path, chat_id)` → 세션 디렉토리 전체 삭제
- [ ] `log_conversation(session_dir, role, content)` → 마크다운 append
- [ ] `list_workspace_files(session_dir)` → workspace/ 내 파일 목록 반환

**Task 2.3: Telegram 핸들러 (`src/cclaw/handlers.py`)**
- [ ] `make_handlers(bot_name, bot_path, bot_config) → dict`
- [ ] `/start` 핸들러: 봇 소개 (이름, 성격, 하는 일)
- [ ] `/reset` 핸들러: conversation.md 삭제
- [ ] `/resetall` 핸들러: 세션 디렉토리 전체 삭제
- [ ] `/files` 핸들러: workspace 파일 목록
- [ ] `/status` 핸들러: 세션 상태, 대화 로그 크기
- [ ] `/help` 핸들러: 명령어 목록
- [ ] 일반 메시지 핸들러: `filters.TEXT & ~filters.COMMAND` → Claude Runner
- [ ] 세션별 `asyncio.Lock` (동시 요청 방지)
- [ ] 4096자 메시지 분할 전송
- [ ] `post_init`에서 `set_my_commands` 커맨드 메뉴 자동 등록
- [ ] `allowed_users` 인증 체크

**Task 2.4: Bot Manager (`src/cclaw/bot_manager.py`)**
- [ ] config.yaml에서 봇 목록 로드
- [ ] 봇별 `Application` 인스턴스 생성
- [ ] 모든 봇 동시 polling (`asyncio` 기반)
- [ ] graceful shutdown (SIGINT/SIGTERM)

**Task 2.5: `cclaw start` 구현**
- [ ] 포그라운드 모드: Ctrl+C로 종료
- [ ] `--bot` 옵션: 특정 봇만 실행
- [ ] `--daemon` 플래그: launchd plist 생성 + load
- [ ] 시작 시 안내 메시지: "항상 실행하려면 cclaw start --daemon"

**Task 2.6: `cclaw stop` 구현**
- [ ] launchd unload
- [ ] PID 파일 기반 프로세스 종료

**Task 2.7: `cclaw status` 구현**
- [ ] 데몬 실행 여부 (launchd 상태 또는 PID 체크)
- [ ] 봇별 상태, 세션 수

### Phase 3: 파일 처리

**Task 3.1: 텔레그램 파일 수신**
- [ ] 사진/문서/오디오 핸들러 추가 (`filters.PHOTO | filters.Document.ALL`)
- [ ] 수신 파일을 `workspace/`에 저장
- [ ] 캡션 있으면 캡션 + "파일: workspace/{filename}" 메시지로 Claude Code 호출
- [ ] 캡션 없으면 "workspace/{filename} 파일을 받았습니다" 전달

**Task 3.2: `/send` 커맨드**
- [ ] `/send {filename}` → workspace 파일을 텔레그램 Document로 전송
- [ ] 파일 없으면 에러 메시지
- [ ] `/send` (인자 없이) → 최근 생성 파일 전송 또는 목록 표시

### Phase 4: UX 개선

**Task 4.1: typing 주기적 전송**
- [ ] Claude Code 실행 중 5초 간격 typing action 전송
- [ ] `asyncio.create_task`로 백그라운드 실행

**Task 4.2: `/cancel` 커맨드**
- [ ] 실행 중인 subprocess에 SIGTERM 전송
- [ ] 세션별 process 참조 관리
- [ ] "⛔ 실행 취소됨" 응답

**Task 4.3: 에러 핸들링 강화**
- [ ] Claude Code 미응답 시 타임아웃 메시지
- [ ] 네트워크 끊김 시 자동 재연결 (python-telegram-bot 내장)
- [ ] 봇 토큰 에러 시 해당 봇 스킵, 나머지 실행

**Task 4.4: 로깅**
- [ ] Python logging → `~/.cclaw/logs/cclaw-yymmdd.log` (일별 로테이션)
- [ ] `cclaw logs` 커맨드 → 오늘 로그 `tail -f`
- [ ] 봇별, 세션별 로그 구분

**Task 4.5: 밀린 메시지 큐잉**
- [ ] Mac 재시작 후 대량 수신 대응 전략 설계
- [ ] 세션별 순차 처리 보장

---

## 실행 예시

```bash
# 설치
uv sync

# 온보딩
uv run cclaw init

# 봇 추가
uv run cclaw bot add

# 봇 목록
uv run cclaw bot list

# 실행
uv run cclaw start

# 환경 점검
uv run cclaw doctor
```

---

## 구현 순서 요약

```
Phase 1 (온보딩)   →  cclaw init, cclaw bot add/list/remove, cclaw doctor
Phase 2 (코어+데몬) →  cclaw start/stop/status → 텔레그램 대화 → Claude Code 응답 → 데몬 상시 실행
Phase 3 (파일)     →  텔레그램 파일 수신/전송
Phase 4 (UX)       →  typing, /cancel, 에러 처리, 로깅, 큐잉
```

Phase 1 + Phase 2 완성 시 상시 실행 가능한 MVP.
