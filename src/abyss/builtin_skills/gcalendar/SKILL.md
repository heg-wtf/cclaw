# Google Calendar

`gog` CLI로 Google Calendar 조작. **Always confirm before creating/modifying events** (날짜·시간·제목·참석자 확인 후 승인). 삭제 금지 (취소/거절 제안). 초대 수락/거절도 사용자 승인 필요.

## Commands

```
gog calendar events --today [--json]
gog calendar events --from 'YYYY-MM-DD' --to 'YYYY-MM-DD' [--json]
gog calendar events --upcoming [--limit N] [--json]
gog calendar events --from 'YYYY-MM-DD' --to 'YYYY-MM-DD' --detect-conflicts [--json]
gog calendar event get <eventId> [--json]
gog calendar event create --title 'T' --start '2026-02-25T14:00:00' --end '2026-02-25T15:00:00' [--description] [--location] [--attendee 'email'] [--all-day]
gog calendar event update <eventId> [--title] [--start] [--end] [--description] [--location]
gog calendar event rsvp <eventId> --status accepted|declined|tentative
gog calendar freebusy --from 'datetime' --to 'datetime' [--attendee 'email'] [--json]
gog calendar list [--json]
```

## Notes
- 날짜/시간: ISO 8601 (`2026-02-25T14:00:00`), 종일: `YYYY-MM-DD` + `--all-day`
- `--attendee`: 복수 지정 가능 (반복 사용)
- "몇 시에 비어있어?" → `freebusy` 사용
- 미팅 제안 시 먼저 `freebusy`로 충돌 확인
