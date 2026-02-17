# TODO

## 완료

### Phase 1: 온보딩
- [x] pyproject.toml, uv 프로젝트 초기화
- [x] Typer CLI 뼈대 (init, start, stop, status, doctor, bot add/list/remove/edit)
- [x] 설정 모듈 (config.yaml, bot.yaml, CLAUDE.md 생성)
- [x] 온보딩 마법사 (환경 점검, 토큰 검증, 봇 프로필 생성)
- [x] doctor 커맨드
- [x] bot add/list/remove 커맨드

### Phase 2: 코어 엔진
- [x] Claude Runner (async subprocess `claude -p`)
- [x] 세션 관리 (디렉토리 생성, 대화 로그, workspace)
- [x] Telegram 핸들러 (/start, /reset, /resetall, /files, /status, /help, /version, 메시지)
- [x] Bot Manager (멀티봇 polling, graceful shutdown)
- [x] start/stop/status CLI 커맨드
- [x] launchd 데몬 지원

### Phase 3: 파일 처리
- [x] 텔레그램 파일 수신 (사진/문서 → workspace/ 저장)
- [x] 캡션 있으면 캡션 + 파일 경로로 Claude Code 호출
- [x] `/send` 커맨드 (workspace 파일 → 텔레그램 전송)

### Phase 4: UX 개선
- [x] typing 액션 주기적 전송 (Claude Code 실행 중 4초 간격)
- [x] Markdown → Telegram HTML 변환 (bold, italic, code, heading, link)
- [x] 명령어 이모지 추가
- [x] `/cancel` 커맨드 (실행 중인 subprocess SIGTERM, 프로세스 추적)
- [x] `/model` 커맨드 (모델 조회/변경, bot.yaml 저장)
- [x] `cclaw bot model` CLI 커맨드 (모델 조회/변경)
- [x] 에러 핸들링 강화 (타임아웃 메시지, 개별 봇 오류 격리)
- [x] 로깅 개선 (일별 로테이션, `cclaw logs` / `cclaw logs -f`)
- [x] 메시지 큐잉 (동시 요청 시 대기 + "Message queued" 알림)

### Phase 5: 스킬 시스템
- [x] 스킬 데이터 구조 (`skill.py`: 인식, 로딩, 생성, 삭제, 상태 관리)
- [x] 스킬 CLI 커맨드 (`cclaw skill add/list/remove/setup/test/edit`)
- [x] 봇-스킬 연결 (`attach_skill_to_bot`, `detach_skill_from_bot`)
- [x] CLAUDE.md 조합 (`compose_claude_md`: 봇 프로필 + 스킬 내용 합성)
- [x] Telegram `/skill` 핸들러 (list/attach/detach)
- [x] MCP 스킬 지원 (`.mcp.json` 생성, `merge_mcp_configs`)
- [x] CLI 스킬 환경변수 주입 (`collect_skill_environment_variables`)
- [x] 봇 시작 시 CLAUDE.md 재생성 (`regenerate_bot_claude_md`)
- [x] 세션 CLAUDE.md 전파 (`update_session_claude_md`)

## 미구현 (향후 고려)

### Phase 6: 고급 기능
- [ ] 세션 내보내기/가져오기
- [ ] 봇 간 세션 공유
- [ ] 웹훅 모드 (Long Polling 대안)
- [ ] 멀티 유저 권한 체계 (admin/user 역할 분리)
- [ ] 대화 요약 커맨드 (`/summary`)
- [ ] 자동 세션 정리 (오래된 세션 아카이브/삭제)
