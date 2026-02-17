# 아키텍처

## 전체 구조

```
Telegram ←→ python-telegram-bot (Long Polling) ←→ handlers.py ←→ claude_runner.py ←→ Claude Code CLI
                                                       ↕                 ↕
                                                  session.py         skill.py
                                                       ↕                 ↕
                                              ~/.cclaw/bots/      ~/.cclaw/skills/
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

### 7. 스킬 시스템

봇에 도구/지식을 연결하여 기능을 확장한다.

- 스킬의 최소 단위: 폴더 + `SKILL.md` 하나
- **마크다운 전용 스킬**: `SKILL.md`만 있으면 즉시 active. 봇에 지식/지시를 추가
- **도구 기반 스킬**: `skill.yaml`로 유형(cli/mcp/browser), 필요 명령어, 환경변수 정의. `cclaw skill setup`으로 활성화
- 스킬 연결 시 `compose_claude_md()`로 봇 프롬프트 + 스킬 내용을 합성하여 CLAUDE.md 재생성
- MCP 스킬: 세션 디렉토리에 `.mcp.json` 자동 생성
- CLI 스킬: subprocess 실행 시 환경변수 자동 주입

### 8. Cron 스케줄 자동화

정해진 시간에 Claude Code를 자동 실행하고 결과를 텔레그램으로 전송한다.

- `cron.yaml`에 job 목록 정의 (schedule 또는 at)
- **반복 job**: 표준 cron 표현식 (`0 9 * * *` = 매일 오전 9시)
- **일회성 job**: `at` 필드에 ISO datetime 또는 duration(`30m`, `2h`, `1d`)
- `croniter` 라이브러리로 cron 표현식 유효성 검증 및 매칭
- 스케줄러 루프: 30초마다 현재 시각과 job schedule 비교
- 중복 실행 방지: 마지막 실행 시각을 메모리에 기록, 같은 분에 재실행 방지
- 결과 전송: `bot.yaml`의 `allowed_users` 전원에게 텔레그램 DM 발송
- 격리된 작업 디렉토리: `cron_sessions/{job_name}/`에서 Claude Code 실행
- one-shot job: `delete_after_run=true` 시 실행 후 자동 삭제
- 봇별 스킬/모델 설정 상속, job 레벨에서 오버라이드 가능

## 모듈 의존성

```
cli.py
├── onboarding.py → config.py
├── bot_manager.py
│   ├── config.py
│   ├── skill.py (regenerate_bot_claude_md)
│   ├── cron.py (list_cron_jobs, run_cron_scheduler)
│   ├── handlers.py
│   │   ├── claude_runner.py
│   │   │   └── skill.py (merge_mcp_configs, collect_skill_environment_variables)
│   │   ├── cron.py (list_cron_jobs, get_cron_job, execute_cron_job, next_run_time)
│   │   ├── skill.py (attach/detach, is_skill, skill_status)
│   │   ├── session.py
│   │   ├── config.py (save_bot_config, VALID_MODELS)
│   │   └── utils.py
│   └── utils.py
├── cron.py → config.py, claude_runner.py, utils.py
├── skill.py → config.py (순환 참조: config.py → skill.py는 lazy import로 해결)
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

### /skills 명령
```
수신 → 권한 체크 → list_skills() → bots_using_skill()로 연결 상태 조회 → 전체 스킬 목록 응답
```

### /skill attach 명령
```
수신 → 권한 체크 → is_skill() → skill_status() == "active" 확인 → attach_skill_to_bot() → 메모리 bot_config 동기화 → 응답
```

### Cron 스케줄러
```
봇 시작 → cron.yaml 로드 → asyncio.create_task(run_cron_scheduler) → 30초 주기 루프
  → 현재 시각과 schedule 매칭 → execute_cron_job → run_claude → allowed_users에게 결과 전송
```

### /cron run 명령
```
수신 → 권한 체크 → get_cron_job() → execute_cron_job() → 결과 전송
```
