# Apple Reminders

macOS 미리알림(Reminders) 연동 스킬. `reminders` CLI 도구를 사용하여 미리알림을 조회, 생성, 완료합니다.

## 사용 가능한 명령어

### 리스트 목록 조회

```bash
reminders show-lists
```

### 특정 리스트의 미리알림 조회

```bash
reminders show <list_name>
reminders show <list_name> --include-completed
```

### 미리알림 생성

```bash
reminders add <list_name> "<title>"
reminders add <list_name> "<title>" --due-date "2026-02-22"
reminders add <list_name> "<title>" --due-date "tomorrow 9am" --priority high
reminders add <list_name> "<title>" --notes "메모 내용"
```

### 미리알림 완료

```bash
reminders complete <list_name> <index>
```

### 미리알림 삭제

```bash
reminders delete <list_name> <index>
```

### 오늘 할 일 조회

```bash
reminders show-all --due-date today
```

### 지난 미리알림 조회

```bash
reminders show-all --include-overdue
```

## 사용 가이드라인

- 미리알림 목록이 여러 개일 수 있으므로, 먼저 show-lists로 목록을 확인하세요.
- 미리알림 생성 전에 사용자에게 제목, 리스트, 날짜를 확인하세요.
- 완료/삭제 전에 반드시 사용자에게 확인을 받으세요.
- 인덱스는 show 명령의 출력에서 확인할 수 있습니다.
