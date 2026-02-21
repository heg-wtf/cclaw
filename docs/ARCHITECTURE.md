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

### 9. Heartbeat (주기적 상황 인지)

주기적으로 Claude Code를 깨워 HEARTBEAT.md 체크리스트를 실행하고, 알릴 것이 있을 때만 텔레그램에 메시지를 보내는 프로액티브 에이전트 기능.

- `bot.yaml`의 `heartbeat` 섹션에 설정 (봇당 1개)
- **interval_minutes**: 실행 간격 (기본 30분)
- **active_hours**: 활성 시간 범위 (HH:MM, 로컬 시간 기준, 자정 넘김 지원)
- `HEARTBEAT.md`: 사용자가 편집 가능한 체크리스트 템플릿
- **HEARTBEAT_OK 감지**: 응답에 `HEARTBEAT_OK` 마커 포함 시 알림 없이 로그만 기록
- HEARTBEAT_OK가 없으면 `allowed_users` 전원에게 텔레그램 DM 발송
- 봇에 연결된 스킬 전체를 heartbeat에서도 사용 (별도 스킬 목록 없음)
- 스케줄러 루프에서 매 주기마다 `bot.yaml`을 재읽기하여 런타임 설정 변경 반영
- 격리된 작업 디렉토리: `heartbeat_sessions/`에서 Claude Code 실행

### 10. 빌트인 스킬 시스템

자주 사용하는 스킬을 패키지 내부에 템플릿으로 포함하여 `cclaw skills install`로 쉽게 설치할 수 있다.

- `src/cclaw/builtin_skills/` 디렉토리에 스킬 템플릿 저장 (SKILL.md, skill.yaml 등)
- `builtin_skills/__init__.py`에서 하위 디렉토리를 스캔하여 레지스트리 제공
- `install_builtin_skill()`로 템플릿 파일을 `~/.cclaw/skills/<name>/`에 복사
- 설치 후 요구사항 체크 → 통과하면 자동 활성화, 실패하면 inactive 상태로 안내
- `skill.yaml`의 `install_hints` 필드로 누락 도구의 설치 방법 안내
- 첫 번째 빌트인 스킬: iMessage (`imsg` CLI 도구 활용)
- `cclaw skills` 명령에서 미설치 빌트인 스킬도 함께 표시
- Telegram `/skills` 핸들러에서도 미설치 빌트인 스킬 표시

### 11. 스트리밍 응답

Claude Code의 출력을 실시간으로 Telegram에 전달한다. 사용자가 on/off 토글 가능.

- `bot.yaml`의 `streaming` 필드로 on/off 제어 (기본값: `DEFAULT_STREAMING = True`)
- Telegram `/streaming on|off` 커맨드 또는 CLI `cclaw bot streaming <name> on|off`로 런타임 토글
- **스트리밍 모드** (`_send_streaming_response`):
  - `run_claude_streaming()`: `--output-format stream-json --verbose --include-partial-messages`로 실행
  - stream-json의 `content_block_delta` 이벤트에서 `text_delta`를 추출하여 토큰 단위 스트리밍
  - `on_text_chunk` 콜백으로 핸들러에 텍스트 조각 전달
  - Telegram 메시지를 실시간 편집. 커서 마커(`▌`)로 진행 중 표시
  - 스로틀링(0.5초)으로 Telegram API rate limit 회피
  - 응답 완료 시 Markdown→HTML 변환된 최종 텍스트로 교체
  - 폴백: `result` 이벤트가 없으면 누적된 스트리밍 텍스트 또는 `assistant` 턴 텍스트 사용
- **비스트리밍 모드** (`_send_non_streaming_response`):
  - `run_claude()`: typing 액션 4초 주기 전송 → 완료 후 Markdown→HTML 변환 → 일괄 전송
  - cron, heartbeat와 동일한 기존 Phase 3 방식

## 모듈 의존성

```
cli.py
├── onboarding.py → config.py
├── bot_manager.py
│   ├── config.py
│   ├── skill.py (regenerate_bot_claude_md)
│   ├── cron.py (list_cron_jobs, run_cron_scheduler)
│   ├── heartbeat.py (run_heartbeat_scheduler)
│   ├── handlers.py
│   │   ├── claude_runner.py
│   │   │   └── skill.py (merge_mcp_configs, collect_skill_environment_variables)
│   │   ├── cron.py (list_cron_jobs, get_cron_job, execute_cron_job, next_run_time)
│   │   ├── heartbeat.py (get/enable/disable_heartbeat, execute_heartbeat)
│   │   ├── skill.py (attach/detach, is_skill, skill_status)
│   │   ├── builtin_skills (list_builtin_skills)
│   │   ├── session.py
│   │   ├── config.py (save_bot_config, VALID_MODELS)
│   │   └── utils.py
│   └── utils.py
├── cron.py → config.py, claude_runner.py, utils.py
├── heartbeat.py → config.py, claude_runner.py, utils.py
├── skill.py → config.py, builtin_skills (순환 참조: config.py → skill.py는 lazy import로 해결)
├── builtin_skills → (패키지 내부 템플릿, 외부 의존성 없음)
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
수신 → 권한 체크 → 세션 Lock (큐잉) → ensure_session → streaming_enabled 분기
  → (스트리밍 on) run_claude_streaming → 토큰별 메시지 편집 → Markdown→HTML 변환 → 최종 메시지 교체/분할 전송
  → (스트리밍 off) typing 액션 4초 주기 → run_claude → Markdown→HTML 변환 → 일괄 전송
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
수신 → 권한 체크 → args 분기
  → (없음 또는 "list"): list_skills() → bots_using_skill()로 연결 상태 조회 → list_builtin_skills()로 미설치 빌트인 포함 → 전체 스킬 목록 응답
  → "attach <name>": is_skill() → skill_status() == "active" 확인 → attach_skill_to_bot() → 메모리 bot_config 동기화 → 응답
  → "detach <name>": detach_skill_from_bot() → 메모리 bot_config 동기화 → 응답
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

### Heartbeat 스케줄러
```
봇 시작 → heartbeat.enabled 확인 → asyncio.create_task(run_heartbeat_scheduler) → interval_minutes 주기 루프
  → active_hours 범위 확인 → 범위 밖이면 스킵
  → HEARTBEAT.md 로드 → run_claude → 응답에 HEARTBEAT_OK 포함 여부 확인
  → HEARTBEAT_OK 있으면 로그만 기록
  → HEARTBEAT_OK 없으면 allowed_users에게 텔레그램 전송
```

### /streaming 명령
```
수신 → 권한 체크 → 인자 분기
  → (없음): streaming_enabled 현재 상태 표시
  → on: streaming_enabled = True, bot.yaml 저장
  → off: streaming_enabled = False, bot.yaml 저장
```

### /heartbeat 명령
```
수신 → 권한 체크 → subcommand 분기
  → (없음): get_heartbeat_config() → 상태 표시
  → on: enable_heartbeat() → 활성화 (HEARTBEAT.md 자동 생성)
  → off: disable_heartbeat() → 비활성화
  → run: execute_heartbeat() → 즉시 실행
```
