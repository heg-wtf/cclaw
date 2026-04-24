# Jira

Jira MCP. 이슈 검색, 생성, 수정, 상태 전환.

**Always confirm before creating/transitioning issues.** 생성 전 프로젝트·유형·제목 확인 후 승인. 상태 전환 전 현재→목표 확인 후 승인. 일괄 수정 금지. 삭제 금지 (닫기 제안).

## Operations

### jira_search — JQL 검색
```
project = PROJ
assignee = currentUser()
status = "In Progress"
priority = High AND status != Done
created >= -7d
text ~ "keyword"
sprint in openSprints()
```

### jira_get_issue — 상세 조회
이슈 키 (예: `PROJ-123`) → summary, description, status, assignee, comments

### jira_create_issue — 생성
필수: project key, issue type(Bug/Task/Story/Epic), summary. 선택: description, assignee, priority, labels

### jira_update_issue — 수정
이슈 키 + 변경할 필드. 변경 내용을 보여주고 승인 후 실행

### jira_transition_issue — 상태 전환
이슈 키 + 목표 상태. 일반 흐름: To Do → In Progress → In Review → Done

## Notes
- 이슈 키 언급 시 먼저 `jira_get_issue`로 상세 확인
- JQL과 필드명은 영문, 사용자 응답은 한국어
