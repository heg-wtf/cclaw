# iMessage

macOS iMessage/SMS. `imsg` CLI + `osascript` 연락처 조회. **전송 전 반드시 수신자·내용 확인 후 사용자 승인.**

## Contact Lookup

이름으로 요청 시 먼저 연락처에서 전화번호를 조회:

```bash
osascript -e 'tell application "Contacts" to get {name, value of phones} of every person whose name contains "검색어"'
```

- 부분 일치 지원 ("John" → "John Smith" 매치)
- 복수 결과 시 사용자에게 확인
- 조회된 번호로 `imsg send --to +821012345678 --text "message"` 실행

## Commands

```
imsg chats [--limit N] [--json]                          # 대화 목록
imsg history --chat-id <id> [--limit N] [--json]         # 메시지 이력
imsg send --to <handle> [--text "msg"] [--file /path]    # 메시지/파일 전송
imsg watch [--chat-id <id>] [--json]                     # 실시간 모니터링
```

## Notes
- 전화번호: `+821012345678` (국제 형식)
- 파일 전송 시 절대 경로 사용
- `--json`: 구조화된 파싱 필요시
