# 기술적 유의사항

## CCLAW_HOME 환경변수

런타임 데이터 경로는 기본값 `~/.cclaw/`이며, `CCLAW_HOME` 환경변수로 변경 가능하다.
테스트에서는 `monkeypatch.setenv("CCLAW_HOME", str(tmp_path))`로 격리한다.

## 경로 관리 원칙

모든 경로는 절대경로를 사용한다. `config.py`의 `bot_directory(name)` 함수가 `cclaw_home() / "bots" / name` 절대경로를 반환하며, 다른 모듈에서는 이 함수를 통해 봇 디렉토리에 접근한다. `config.yaml`의 봇 엔트리에도 절대경로가 저장된다. 상대경로 사용을 지양하고, 경로 조합에는 `pathlib.Path`를 사용한다.

## Telegram 메시지 제한

Telegram 메시지는 최대 4096자. `utils.split_message()`로 긴 응답을 분할 전송한다.
줄바꿈 경계에서 분할을 시도하고, 적절한 줄바꿈이 없으면 한도에서 잘라낸다.

## Claude Code 실행

두 가지 실행 모드를 지원한다:

- **일반 모드**: `claude -p "<message>" --output-format text` (cron, heartbeat 등)
- **스트리밍 모드**: `claude -p "<message>" --output-format stream-json --verbose --include-partial-messages` (Telegram 대화)

작업 디렉토리는 subprocess의 `cwd` 파라미터로 세션 디렉토리를 지정한다.

- `shutil.which("claude")`로 Claude CLI 전체 경로를 해석한다. `uv run`, `pip install`, `pipx install` 등 설치 방법에 관계없이 PATH에서 claude를 찾는다. 경로를 찾지 못하면 설치 안내와 함께 `RuntimeError`를 발생시킨다.
- `--output-format text`: JSON이 아닌 텍스트 출력
- `--model <model>`: 모델 선택 (sonnet/opus/haiku). `model` 파라미터가 None이면 플래그를 추가하지 않는다.
- `bot.yaml`의 `claude_args` 필드로 추가 인자 전달 가능
- 기본 타임아웃: 300초 (`config.yaml`의 `command_timeout`)

## 모델 선택

- 유효 모델: `VALID_MODELS = ["sonnet", "opus", "haiku"]`, 기본값: `DEFAULT_MODEL = "sonnet"`
- `bot.yaml`의 `model` 필드에 저장. Telegram `/model` 커맨드로 런타임 변경 가능.
- 핸들러 클로저 내에서 `nonlocal current_model`로 런타임 변경을 반영한다.
- 모델 변경 시 `save_bot_config()`로 bot.yaml에 즉시 저장한다.
- CLI에서도 `cclaw bot model <name> [model]`로 조회/변경 가능.

## 프로세스 추적 (/cancel)

- `_running_processes` 모듈 레벨 딕셔너리에 `{bot_name}:{chat_id}` → subprocess 매핑
- `run_claude()` 호출 시 `session_key`를 전달하면 프로세스를 자동 등록/해제
- `/cancel` 명령 시 `cancel_process()`로 `process.kill()` 호출 (SIGKILL)
- 프로세스가 kill된 경우 `returncode == -9` → `asyncio.CancelledError` 발생
- 핸들러에서 `CancelledError`를 catch하여 "Execution was cancelled" 메시지 전송

## 세션 Lock과 메시지 큐잉

같은 채팅에서 동시 요청이 오면 `asyncio.Lock`으로 순차 처리한다.
Lock이 잡혀 있으면 "Message queued. Processing previous request..." 알림을 보낸 후 대기한다.
Lock 키는 `{bot_name}:{chat_id}` 형식이다.

## /send 커맨드

workspace 파일을 텔레그램으로 전송하는 커맨드.
- `/send` (인자 없음): 사용 가능한 파일 목록 표시
- `/send <filename>`: 해당 파일을 `reply_document()`로 전송
- 파일이 존재하지 않으면 "File not found" 메시지 반환

## launchd 데몬

`cclaw start --daemon`은 `~/Library/LaunchAgents/com.cclaw.daemon.plist`를 생성하고 `launchctl load`한다.
`KeepAlive`가 설정되어 있어 프로세스가 종료되면 자동 재시작된다.
`cclaw stop`은 `launchctl unload` 후 plist를 삭제한다.

## 봇 오류 격리

`bot_manager.py`에서 개별 봇의 설정 오류나 시작 실패가 다른 봇에 영향을 주지 않는다.
- 설정 로드/토큰 오류: 해당 봇을 스킵하고 다음 봇 진행
- polling 시작 실패: 해당 봇만 스킵, 나머지 봇은 정상 실행
- `started_applications` 리스트로 실제 시작된 봇만 추적하여 종료 시 정리

## 테스트에서 Telegram API Mock

`telegram.Bot`은 함수 내부에서 import되므로 `patch("telegram.Bot")`으로 mock한다.
`AsyncMock`을 사용하여 `get_me()` 등 async 메서드를 mock 처리한다.

## allowed_users

`bot.yaml`의 `allowed_users`가 빈 리스트이면 모든 사용자를 허용한다.
특정 사용자만 허용하려면 Telegram user ID(정수)를 리스트에 추가한다.

## Markdown → Telegram HTML 변환

Claude의 Markdown 응답을 Telegram HTML로 변환하여 전송한다 (`utils.markdown_to_telegram_html()`).

- `[text](url)` → `<a href="url">text</a>` (링크는 HTML escape 전에 추출하여 URL 보존)
- `**bold**` → `<b>bold</b>`
- `*italic*` → `<i>italic</i>`
- `` `code` `` → `<code>code</code>`
- ` ```code blocks``` ` → `<pre>code blocks</pre>`
- `## heading` → `<b>heading</b>` (Telegram에 heading이 없으므로 bold 처리)
- HTML 전송 실패 시 plain text 폴백

## 스트리밍 on/off 토글

- `bot.yaml`의 `streaming` 필드: `true`(기본값) 또는 `false`
- 기본값 상수: `config.py`의 `DEFAULT_STREAMING = True`
- 핸들러 클로저 내에서 `nonlocal streaming_enabled`로 런타임 변경을 반영한다.
- Telegram `/streaming on|off` 커맨드로 런타임 토글, `save_bot_config()`로 즉시 저장.
- CLI에서도 `cclaw bot streaming <name> [on|off]`로 조회/변경 가능.
- `message_handler`와 `file_handler`에서 `streaming_enabled` 여부에 따라 `_send_streaming_response()` 또는 `_send_non_streaming_response()`를 호출한다.
- 비스트리밍 모드: typing 액션 4초 주기 전송 + `run_claude()` + Markdown→HTML 변환 + 분할 전송 (Phase 3 패턴 복원).

## 스트리밍 응답

### 실행 모드

`run_claude_streaming()`은 `--output-format stream-json --verbose --include-partial-messages` 플래그로 Claude Code를 실행한다.
stdout을 줄 단위로 읽으며 JSON 이벤트를 파싱한다.

### stream-json 이벤트 파싱

세 가지 이벤트 유형을 처리한다:

- `stream_event` + `content_block_delta` + `text_delta`: 토큰 단위 텍스트 (--verbose 모드)
- `assistant` 메시지의 `content` 블록: 턴 레벨 텍스트 (폴백)
- `result`: 최종 완성 텍스트

`result` 이벤트의 텍스트를 우선 사용하고, 없으면 누적된 스트리밍 텍스트를 사용한다.

### Telegram 메시지 편집 전략

- 최소 10자(`STREAM_MIN_CHARS_BEFORE_SEND`) 누적 후 첫 `reply_text()` 전송
- 이후 0.5초(`STREAM_THROTTLE_SECONDS`) 간격으로 `edit_message_text()` 호출
- 커서 마커 `▌`(`STREAMING_CURSOR`)를 텍스트 끝에 추가하여 진행 중 표시
- 4096자 초과 시 스트리밍 미리보기 중단 (`stream_stopped = True`)
- 응답 완료 시: 단일 청크면 HTML 포맷으로 메시지 편집, 복수 청크면 미리보기 삭제 후 분할 전송

### typing 액션

스트리밍 미지원 경로(cron, heartbeat) 및 스트리밍 off 상태의 대화 메시지에서는 typing 액션 방식을 사용한다.
4초 간격으로 `send_action("typing")` 전송, `asyncio.create_task`로 백그라운드 실행.

## 파일 수신

사진/문서를 수신하면 workspace에 다운로드 후 Claude에게 파일 경로와 함께 전달한다.
사진은 가장 큰 사이즈(`photo[-1]`)를 선택한다.

## 스킬 시스템

### 스킬 유형

- **마크다운 전용** (`skill.yaml` 없음): `SKILL.md`만 있으면 항상 active. 별도 설정 불필요.
- **도구 기반** (`skill.yaml` 있음): `type`이 cli/mcp/browser. 초기 상태 inactive. `cclaw skill setup`으로 요구사항 확인 후 active로 전환.

### CLAUDE.md 합성

`compose_claude_md()`가 봇 프로필 + 스킬 SKILL.md 내용을 하나의 CLAUDE.md로 조합한다.
스킬이 없으면 기존 `generate_claude_md()`와 동일한 출력.
`save_bot_config()` 호출 시 자동으로 CLAUDE.md가 재생성된다.
봇 시작 시에도 `regenerate_bot_claude_md()`로 최신 스킬 상태를 반영한다.

### 순환 참조 해결

`config.py` ↔ `skill.py` 양방향 의존이 발생한다.
`config.py`의 `save_bot_config()` 내에서 `from cclaw.skill import compose_claude_md`를 lazy import로 해결한다.

### MCP 스킬

MCP 스킬은 `mcp.json` 파일에 `mcpServers` 설정을 정의한다.
`run_claude()` 호출 시 `merge_mcp_configs()`로 연결된 모든 MCP 스킬의 설정을 병합하여
세션 디렉토리에 `.mcp.json`을 생성한다. Claude Code가 이를 자동으로 인식한다.

### CLI 스킬 환경변수

CLI 스킬은 `skill.yaml`의 `environment_variable_values`에 값을 저장한다.
`cclaw skill setup`에서 환경변수 값을 입력받는다.
`run_claude()` 호출 시 `collect_skill_environment_variables()`로 수집하여
subprocess의 `env` 파라미터에 주입한다.

### 세션 CLAUDE.md 전파

`ensure_session()`은 기존 동작을 유지한다 (세션 CLAUDE.md가 없을 때만 봇 CLAUDE.md를 복사).
스킬 attach/detach 시 `update_session_claude_md()`가 기존 모든 세션의 CLAUDE.md를 명시적으로 덮어쓴다.

### Telegram /skills 핸들러

`/skills` 커맨드는 `list_skills()`로 설치된 스킬 목록을 조회하고,
`bots_using_skill()`로 각 스킬의 연결 상태를 표시한다.
봇에 연결되지 않은 스킬도 포함된다.
추가로 `list_builtin_skills()`로 미설치 빌트인 스킬도 하단에 표시한다.

## Cron 스케줄 자동화

### cron.yaml 스키마

```yaml
jobs:
  - name: morning-email       # job 식별자
    schedule: "0 9 * * *"     # 표준 cron 표현식
    message: "오늘 아침 이메일 요약해줘"
    skills: [gmail]           # 선택 (없으면 봇 기본 스킬)
    model: haiku              # 선택 (없으면 봇 기본 모델)
    enabled: true
  - name: call-reminder       # 일회성 job
    at: "2026-02-20T15:00:00" # ISO datetime 또는 "30m"/"2h"/"1d"
    message: "클라이언트 콜백 시간입니다"
    delete_after_run: true    # 실행 후 자동 삭제
```

### 스케줄러 동작

- `bot_manager.py`에서 봇 시작 시 `asyncio.create_task(run_cron_scheduler())`로 실행
- 30초 주기로 현재 시각과 job schedule 매칭 확인
- `croniter`의 `get_next()`로 현재 분에 해당하는 fire time 계산
- 마지막 실행 시각을 메모리(`last_run_times` dict)에 기록하여 같은 분에 중복 실행 방지
- `stop_event`로 graceful shutdown (봇 종료 시 cron도 함께 종료)

### 결과 전송

- `bot.yaml`의 `allowed_users` 전원에게 `application.bot.send_message()`로 전송
- DM에서는 user_id == chat_id이므로 별도 채팅 ID 관리 불필요
- `allowed_users`가 비어있으면 전송 스킵 (경고 로그)
- 메시지 앞에 `[cron: job_name]` 헤더 추가

### 작업 디렉토리 격리

- 각 job은 `~/.cclaw/bots/{name}/cron_sessions/{job_name}/` 디렉토리에서 실행
- 봇의 CLAUDE.md를 복사하여 Claude Code가 봇 컨텍스트를 인식
- 일반 세션과 완전히 분리되어 cron job 간 간섭 없음

### one-shot job

- `at` 필드가 있으면 schedule 대신 일회성 실행
- ISO 8601 datetime (`2026-02-20T15:00:00`) 또는 duration shorthand (`30m`, `2h`, `1d`) 지원
- `delete_after_run: true`이면 실행 후 `cron.yaml`에서 자동 삭제

### Telegram /skills 핸들러 (통합)

`/skills` 핸들러가 스킬 목록 표시, attach, detach 기능을 모두 담당한다 (기존 `/skill` 핸들러는 `/skills`로 통합됨).
핸들러 클로저 내 `attached_skills` 변수로 현재 연결된 스킬을 추적한다.
attach/detach 후 로컬 `bot_config["skills"]`를 직접 갱신하여 메모리와 디스크 상태를 동기화한다.
(`attach_skill_to_bot()`은 디스크의 config만 수정하므로, 메모리의 `bot_config`도 별도로 업데이트해야 한다.)
`run_claude()` 호출 시 `skill_names=attached_skills`를 전달한다.
미설치 빌트인 스킬도 `list_builtin_skills()`로 조회하여 목록 하단에 표시한다.

### 빌트인 스킬

`src/cclaw/builtin_skills/` 패키지에 스킬 템플릿을 포함한다.
`install_builtin_skill()`은 `shutil.copy2`로 템플릿 파일을 `~/.cclaw/skills/<name>/`에 복사한다.
`skill.yaml`의 `install_hints` 필드(dict)로 누락 도구의 설치 방법을 안내한다.
`check_skill_requirements()`가 `install_hints`를 읽어 에러 메시지에 `Install: <hint>` 형식으로 포함한다.

## Heartbeat (주기적 상황 인지)

### 설정 위치

cron은 별도 `cron.yaml`을 사용하지만, heartbeat는 `bot.yaml` 내 `heartbeat` 섹션에 저장한다 (봇당 1개).

```yaml
heartbeat:
  enabled: false
  interval_minutes: 30
  active_hours:
    start: "07:00"
    end: "23:00"
```

### HEARTBEAT_OK 마커

`HEARTBEAT_OK_MARKER = "HEARTBEAT_OK"` 문자열이 Claude 응답에 포함되면 알림을 보내지 않는다.
대소문자 정확 매치 (`HEARTBEAT_OK in response`).
HEARTBEAT.md 템플릿에 "HEARTBEAT_OK는 반드시 응답 마지막에 포함할 것" 규칙을 포함한다.

### Active Hours

로컬 시간(`datetime.now()`) 기준 HH:MM 비교.
자정 넘김 지원: `start > end`이면 야간 범위로 간주 (예: 22:00-06:00).

### 스케줄러 동적 설정 반영

`run_heartbeat_scheduler()`는 매 주기마다 `load_bot_config()`로 bot.yaml을 재읽기한다.
Telegram `/heartbeat on`/`off`으로 런타임에 활성/비활성을 변경하면 다음 주기부터 반영된다.

### HEARTBEAT.md 생성 시점

봇 생성 시(`onboarding.py`)에는 `heartbeat` 설정만 bot.yaml에 추가하고 HEARTBEAT.md는 생성하지 않는다.
`cclaw heartbeat enable` 또는 Telegram `/heartbeat on` 실행 시 HEARTBEAT.md가 없으면 기본 템플릿을 자동 생성한다.

### 작업 디렉토리

`~/.cclaw/bots/{name}/heartbeat_sessions/`에서 Claude Code를 실행한다.
봇의 CLAUDE.md를 복사하고, workspace/ 하위 디렉토리를 생성한다.
cron_sessions/와 동일한 격리 패턴.

### 결과 전송

bot.yaml의 `allowed_users` 전원에게 전송한다 (cron과 동일 패턴).
메시지 앞에 `[heartbeat: bot_name]` 헤더를 추가한다.
