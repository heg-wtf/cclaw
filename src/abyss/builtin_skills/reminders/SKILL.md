# Apple Reminders

macOS Reminders. `reminders` CLI. **생성/완료/삭제 전 반드시 사용자 확인.**

## Commands

```
reminders show-lists                                      # 리스트 목록
reminders show <list> [--include-completed]                # 리스트별 리마인더
reminders show-all --due-date today                        # 오늘 할 일
reminders show-all --include-overdue                       # 기한 지난 항목
reminders add <list> "title" [--due-date "2026-02-22"] [--priority high] [--notes "note"]
reminders complete <list> <index>
reminders delete <list> <index>
```

## Notes
- `show-lists`로 먼저 목록 확인 후 작업
- index 번호는 `show` 출력에서 확인
- `--due-date`: 날짜(`2026-02-22`) 또는 자연어(`tomorrow 9am`)
