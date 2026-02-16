# 기술적 유의사항

## CCLAW_HOME 환경변수

런타임 데이터 경로는 기본값 `~/.cclaw/`이며, `CCLAW_HOME` 환경변수로 변경 가능하다.
테스트에서는 `monkeypatch.setenv("CCLAW_HOME", str(tmp_path))`로 격리한다.

## Telegram 메시지 제한

Telegram 메시지는 최대 4096자. `utils.split_message()`로 긴 응답을 분할 전송한다.
줄바꿈 경계에서 분할을 시도하고, 적절한 줄바꿈이 없으면 한도에서 잘라낸다.

## Claude Code 실행

`claude -p "<message>" --output-format text`로 실행한다. 작업 디렉토리는 subprocess의 `cwd` 파라미터로 세션 디렉토리를 지정한다.

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

## typing 액션

Claude Code 실행 중 4초 간격으로 `send_action("typing")`을 전송한다.
`asyncio.create_task`로 백그라운드 실행하고, Claude 응답 완료 시 `task.cancel()`로 중단한다.

## 파일 수신

사진/문서를 수신하면 workspace에 다운로드 후 Claude에게 파일 경로와 함께 전달한다.
사진은 가장 큰 사이즈(`photo[-1]`)를 선택한다.
