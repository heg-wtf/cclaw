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

### Phase 3: 파일 처리 (부분 완료)
- [x] 텔레그램 파일 수신 (사진/문서 → workspace/ 저장)
- [x] 캡션 있으면 캡션 + 파일 경로로 Claude Code 호출
- [ ] `/send` 커맨드 (workspace 파일 → 텔레그램 전송)

### Phase 4: UX 개선 (부분 완료)
- [x] typing 액션 주기적 전송 (Claude Code 실행 중 4초 간격)
- [x] Markdown → Telegram HTML 변환 (bold, italic, code, heading, link)
- [x] 명령어 이모지 추가
- [ ] `/cancel` 커맨드 (실행 중인 subprocess SIGTERM)
- [ ] 에러 핸들링 강화 (타임아웃 메시지, 자동 재연결, 봇 스킵)
- [ ] 로깅 개선 (일별 로테이션, `cclaw logs` tail)
- [ ] 밀린 메시지 큐잉 (Mac 재시작 후 대량 수신 대응)
