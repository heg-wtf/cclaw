# iMessage

macOS iMessage/SMS 연동 스킬. `imsg` CLI 도구를 사용하여 메시지를 확인하고 발송합니다.

## 사용 가능한 명령어

### 대화 목록 조회

```bash
imsg chats [--limit N] [--json]
```

- 최근 대화 목록을 표시합니다
- `--limit N`: 표시할 대화 수 제한 (기본: 20)
- `--json`: JSON 형식으로 출력

### 메시지 히스토리 조회

```bash
imsg history --chat-id <id> [--limit N] [--json]
```

- 특정 대화의 메시지 히스토리를 조회합니다
- `--chat-id`: 대화 ID (chats 명령으로 확인)
- `--limit N`: 표시할 메시지 수 제한 (기본: 50)
- `--json`: JSON 형식으로 출력

### 메시지 발송

```bash
imsg send --to <handle> [--text "message"] [--file /path/to/file]
```

- 메시지 또는 파일을 발송합니다
- `--to`: 수신자 (전화번호 또는 이메일)
- `--text`: 텍스트 메시지
- `--file`: 첨부 파일 경로

### 실시간 모니터링

```bash
imsg watch [--chat-id <id>] [--json]
```

- 새 메시지를 실시간으로 모니터링합니다
- `--chat-id`: 특정 대화만 모니터링 (생략 시 전체)
- `--json`: JSON 형식으로 출력

## 사용 가이드라인

- **메시지 발송 전 반드시 사용자에게 확인을 받으세요.** 절대 확인 없이 메시지를 보내지 마세요.
- `--json` 옵션을 사용하면 구조화된 데이터를 파싱하기 쉽습니다.
- 대화 목록에서 chat-id를 먼저 확인한 후 히스토리를 조회하세요.
- 전화번호 형식: `+821012345678` (국제 형식 권장)
- 파일 발송 시 절대 경로를 사용하세요.
