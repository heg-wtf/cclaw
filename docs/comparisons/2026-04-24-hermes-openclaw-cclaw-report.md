# Hermes, OpenClaw, and cclaw 비교 분석

작성일: 2026-04-24

## 한 줄 결론

세 프로젝트는 모두 "개인 AI"를 지향하지만, 중심축이 다릅니다.

- cclaw: Telegram 중심의 로컬 개인 비서
- Hermes: 도구와 메모리를 갖춘 범용 AI 에이전트 런타임
- OpenClaw: 멀티채널/멀티에이전트/게이트웨이 중심의 AI 운영 플랫폼

즉, cclaw는 실행이 단순하고 Claude Code에 깊게 붙어 있으며, Hermes는 에이전트 기능 폭이 가장 넓고, OpenClaw는 배포/채널/권한/샌드박스까지 포함한 플랫폼 구조가 가장 강합니다.

## 비교 기준

이 문서는 다음 기준으로 세 프로젝트를 비교합니다.

- 런타임과 언어
- 제품 중심축
- 메시징/채널 구조
- 상태 저장 방식
- 도구와 확장성
- 메모리와 지식 축적 방식
- 자동화와 에이전트 오케스트레이션
- 보안과 권한 모델
- Claude 의존도
- 개인 AI 플랫폼으로서의 잠재력

## 1. 각 프로젝트의 구조 요약

### cclaw

cclaw는 Python 기반의 Telegram + Claude Code 개인 비서입니다.

핵심 특징:

- Python 3.11+
- Typer CLI + python-telegram-bot
- Claude Code CLI(`claude -p`)와 Python Agent SDK를 통한 세션 지속
- 상태는 전부 `~/.cclaw/` 아래 파일로 관리
- 봇별 메모리, 전역 메모리, 세션 대화 로그, workspace, cron, heartbeat, group 협업을 지원
- skills로 확장
- ClawHouse라는 Next.js 웹 대시보드 제공

즉, cclaw는 "로컬 파일 기반 상태 + Telegram 인터페이스 + Claude 실행 오케스트레이션"에 최적화되어 있습니다.

### Hermes

Hermes Agent는 훨씬 더 범용적인 에이전트 런타임입니다.

핵심 특징:

- Python 중심 에이전트 런타임
- 자체 툴 레지스트리와 toolset 시스템
- web, terminal, browser, file, memory, delegation, cron, code execution 등 매우 넓은 도구군
- 세션 DB(SQLite + FTS5) 기반의 session search
- `MEMORY.md`와 `USER.md`를 사용하는 bounded persistent memory
- skills, plugins, MCP, provider routing, fallback providers, credential pools 지원
- messaging gateway, TUI, API server, ACP 통합, voice mode, image generation 등 인터페이스가 매우 풍부

즉, Hermes는 "에이전트 실행 엔진 자체"에 더 가깝고, cclaw보다 훨씬 넓은 작업 공간과 도구 생태계를 가집니다.

### OpenClaw

OpenClaw는 TS/Node 기반의 멀티채널 AI gateway입니다.

핵심 특징:

- Node 22/24 기반
- 단일 Gateway가 WhatsApp, Telegram, Slack, Discord, Signal, iMessage 등 여러 메시징 수단을 제어
- WebSocket 기반 control plane
- 노드(role: node)와 게이트웨이 분리
- typed protocol, JSON Schema, pairings, device identity, idempotency, auth mode 등 강한 운영/보안 모델
- plugin SDK, extensions, channels, tools, skills, sandboxing, routing
- multi-agent routing과 delegate architecture
- live canvas, companion apps, voice wake, talk mode 같은 플랫폼 기능

즉, OpenClaw는 "메시징이 중심인 운영 플랫폼"이고, 개인 비서보다 더 큰 조직/디바이스/채널 통합 체계로 설계되어 있습니다.

## 2. 아키텍처 중심축 비교

### cclaw

- 중심축: Telegram 봇 + Claude 실행기
- 주요 목표: 개인 대화, 메모리, 자동화, group collaboration
- 상태 저장: 파일
- 인터페이스: Telegram과 CLI, 웹 대시보드

cclaw는 비교적 작은 배치 단위로 빠르게 이해하고 운영하기 좋습니다.

### Hermes

- 중심축: 에이전트 런타임 + toolsets + memory + session search
- 주요 목표: 범용 에이전트 플랫폼, 다양한 채널/도구/모델 지원
- 상태 저장: SQLite 세션 + 파일 메모리 + skill 디렉터리
- 인터페이스: CLI, TUI, messaging gateway, API server, ACP

Hermes는 "한 명의 에이전트를 어디서나 돌리는 실행 프레임워크"에 가깝습니다.

### OpenClaw

- 중심축: Gateway + channel abstraction + agent routing
- 주요 목표: 여러 메시징 채널과 노드/디바이스를 하나의 제어 평면으로 묶기
- 상태 저장: 게이트웨이/세션/워크스페이스/디바이스 pairing store
- 인터페이스: CLI, web UI, macOS/iOS/Android nodes, web surfaces

OpenClaw는 "개인 비서"보다 "AI 인프라/운영체제"에 더 가깝습니다.

## 3. Claude 의존도와 모델 추상화

### cclaw: Claude 의존도가 가장 큼

cclaw는 Claude Code CLI와 Agent SDK를 중심으로 설계되어 있습니다.

특징:

- `claude -p` subprocess 실행
- resume / session-id 지속
- skill에 따른 allowed tools 주입
- CLAUDE.md를 시스템 지시문 경로로 사용

즉, cclaw는 Claude의 세션/도구/프롬프트 모델에 깊게 결합되어 있습니다.

장점:

- Claude Code의 강점을 그대로 활용 가능
- 세션 continuity를 구현하기 쉽다
- Claude의 system prompt/skills 패턴과 잘 맞는다

단점:

- 모델/런타임에 대한 종속성이 크다
- 다른 모델이나 다른 에이전트 런타임으로 갈아타기 어렵다

### Hermes: 모델과 도구를 더 분리

Hermes는 provider routing, fallback providers, credential pools를 갖고 있어 모델 의존도를 낮추는 편입니다.

특징:

- 여러 provider와 모델을 제어
- web tool gateway / browser / execute_code / delegate_task 등 도구를 런타임 내부에서 통합
- Claude에 꼭 묶이지 않음

즉, Hermes는 "에이전트 로직"과 "모델 공급자"를 분리하려는 성향이 강합니다.

### OpenClaw: 게이트웨이/플러그인 중심

OpenClaw 역시 여러 provider를 다루지만, 핵심은 모델보다 "메시징과 플랫폼 레이어"입니다.

특징:

- gateway protocol과 channel routing이 핵심
- extensions/plugin SDK로 기능을 분리
- model failover와 provider 추상화가 존재

즉, OpenClaw는 Claude 중심이 아니라 플랫폼과 프로토콜 중심입니다.

## 4. 채널과 인터페이스 비교

### cclaw

- Telegram이 메인
- CLI와 웹 대시보드가 보조
- group collaboration은 Telegram 그룹 기반

### Hermes

- CLI가 핵심이지만 messaging gateway가 매우 풍부
- Telegram, Discord, Slack, WhatsApp, Signal, Matrix 등 다수 지원
- TUI, API server, ACP, browser, voice mode까지 포함

### OpenClaw

- 멀티채널이 제품의 중심
- WhatsApp, Telegram, Slack, Discord, Signal, iMessage, WebChat, 그리고 노드 디바이스까지 연결
- 메시징 채널은 Gateway가 모두 조정

요약하면:

- cclaw는 Telegram-first
- Hermes는 interface-agnostic
- OpenClaw는 multi-channel-first

## 5. 상태 저장 방식 비교

### cclaw

가장 단순하고 투명합니다.

- `~/.cclaw/config.yaml`
- `~/.cclaw/bots/<name>/bot.yaml`
- `MEMORY.md`
- `GLOBAL_MEMORY.md`
- `sessions/chat_<id>/conversation-YYYYMMDD.md`
- `workspace/`
- `cron.yaml`, `HEARTBEAT.md`

장점:

- 사람이 직접 들여다보기 쉽다
- 백업/이동/복구가 쉽다
- 로컬 우선 작업에 잘 맞는다

단점:

- DB 기반 질의, 검색, 감사, 동기화에는 한계가 있다
- 구조가 커질수록 파일 수가 많아진다

### Hermes

혼합형입니다.

- session store는 SQLite 기반
- memory는 `MEMORY.md`와 `USER.md`
- skills는 `~/.hermes/skills/`
- session search는 FTS5

장점:

- 검색과 세션 복구에 강하다
- 파일과 DB를 적절히 혼합한다
- memory capacity를 제어하기 쉽다

단점:

- cclaw보다 구조가 더 복잡하다
- 여러 저장 계층을 이해해야 한다

### OpenClaw

플랫폼형 저장 구조입니다.

- Gateway config
- channel/agent/session store
- workspace
- device pairing store
- logs, cron runs, audit trails

장점:

- 운영/감사/권한/세션이 잘 분리됨
- 대규모 멀티채널에 적합

단점:

- 개인용 로컬 툴보다 학습 비용이 높다
- 개념이 많다

## 6. 도구와 확장성 비교

### cclaw

확장 포인트는 skill입니다.

- built-in skills
- custom skills
- GitHub import
- skill.yaml + SKILL.md + mcp.json
- allowed_tools와 환경변수 주입

강점:

- 구조가 간단하다
- Claude 실행 정책과 잘 맞는다
- Telegram 비서용으로 실용적이다

한계:

- tool 생태계는 Hermes/OpenClaw보다 좁다
- platform-level plugin model은 아니다

### Hermes

가장 풍부합니다.

- 47개 내장 도구군
- toolsets 기반 활성화/비활성화
- browser, web, file, memory, cron, delegation, code execution, image generation, TTS, MCP, Home Assistant, RL training 등
- plugins와 memory providers까지 포함

강점:

- 개인 에이전트 실험에 매우 유리
- 기능 조합이 풍부하다
- 범용성이 높다

### OpenClaw

확장성이 플랫폼 수준입니다.

- plugin SDK
- bundled extensions
- channel extensions
- node/agent extensions
- sandbox와 routing contracts

강점:

- "플러그인 생태계"를 만들기 좋다
- 채널/디바이스/권한/자동화를 분리해 확장할 수 있다

## 7. 메모리와 지식 축적

### cclaw

- 봇별 MEMORY.md
- GLOBAL_MEMORY.md
- conversation logs
- QMD가 있으면 로컬 문서 검색 가능

이 구조는 단순하고 이해하기 쉽지만, 기억을 체계화하는 계층은 비교적 얇습니다.

### Hermes

- MEMORY.md + USER.md의 이원 구조
- 세션 검색(SQLite FTS5)
- 외부 memory provider 플러그인
- LLM이 직접 메모리를 관리하는 설계

즉, Hermes는 메모리 자체를 제품의 핵심 기능으로 다룹니다.

### OpenClaw

- session model과 AGENTS.md/SOUL.md/USER.md 같은 context file 기반 설계
- 프로덕션 운영과 권한 경계에 맞춘 설계

즉, OpenClaw는 기억보다 "정책과 운영"에 더 무게가 있습니다.

## 8. 자동화와 에이전트 오케스트레이션

### cclaw

- cron
- heartbeat
- group orchestrator/member 구조
- resume/reset/cancel 세션 제어

즉, 개인 비서와 소규모 팀 협업에 잘 맞습니다.

### Hermes

- cronjob
- delegate_task
- execute_code
- batch processing
- hooks
- tool gateway

즉, 자동화와 실험이 매우 강합니다.

### OpenClaw

- cron jobs
- standing orders
- multi-agent routing
- delegate architecture
- gateway 이벤트/웹훅/원격 제어

즉, "운영 가능한 autonomous system"을 만드는 데 초점이 있습니다.

## 9. 보안과 권한 모델

### cclaw

- 기본적으로 로컬-first
- allowlist된 Claude 도구와 skill별 allowed_tools로 권한을 조절
- 하지만 현재 코드베이스는 경로 검증/권한 검증/환경변수 주입 측면에서 주의가 필요함

즉, 작고 실용적이지만 보안 경계는 상대적으로 얇습니다.

### Hermes

- terminal backend를 분리할 수 있음
- docker, ssh, singularity, modal, daytona 지원
- sandbox, prompt caching, hooks, approval 체계가 있음
- 기능이 많은 만큼 설정이 중요

즉, 실험성과 안전성을 모두 고려한 구조입니다.

### OpenClaw

가장 강한 보안/권한 모델을 보여줍니다.

- Gateway auth
- device pairing
- role: node
- JSON Schema 검증
- idempotency key
- sandboxing
- delegation permissions
- org-level trust boundary

즉, OpenClaw는 보안과 운영을 제품의 핵심 축으로 놓고 있습니다.

## 10. 개인 AI 플랫폼으로서의 적합성

### cclaw가 잘하는 것

- 개인이 Telegram에서 쉽게 쓰는 비서
- 로컬 파일 기반이라 가볍고 투명함
- Claude Code와 잘 맞는 워크플로우
- 작은 팀/그룹 협업에도 적당함

### Hermes가 잘하는 것

- 강력한 범용 에이전트 런타임
- 다양한 모델/도구/인터페이스를 실험 가능
- memory, delegation, browser, code execution, TTS, vision까지 폭이 넓음
- 개인 AI 플랫폼의 "기능 실험실"에 적합

### OpenClaw가 잘하는 것

- 멀티채널 운영
- 게이트웨이/노드/플러그인/보안/권한이 분리된 진짜 플랫폼 구조
- 개인 사용을 넘어서 조직 운영과 디바이스 협업으로 확장 가능

## 11. cclaw 입장에서 배울 점

cclaw가 개인 AI 플랫폼으로 더 발전하려면, 두 프로젝트에서 다음을 가져오면 좋습니다.

### Hermes에서 배울 점

- 세션 검색과 메모리 계층화
- toolsets 기반 권한 관리
- browser / code execution / delegate 같은 범용 에이전트 도구
- 외부 memory provider와 plugins
- provider routing과 fallback 구조

### OpenClaw에서 배울 점

- gateway/transport 분리
- 더 명확한 auth / pairing / audit trail
- agent role 분리와 sandbox 경계
- channel abstraction
- multi-agent routing과 node 개념

### cclaw의 강점을 유지해야 하는 점

- 파일 기반 단순성
- Claude Code 중심의 자연스러운 세션 지속성
- Telegram-first의 낮은 운영 비용
- 빠른 로컬 디버깅과 투명한 데이터 구조

## 12. 종합 평가

### cclaw

장점:

- 단순하고 실용적
- Claude Code와 매우 잘 결합됨
- 개인 사용에 빠르게 적용 가능

약점:

- Claude 의존도가 높음
- 플랫폼 수준 확장성은 아직 제한적
- 보안/권한 모델은 더 강화할 여지가 큼

### Hermes

장점:

- 에이전트 기능이 매우 풍부함
- toolsets / memory / delegation / MCP / browser / TTS 등 범용성 최고 수준
- 개인 AI 실험 플랫폼으로 강력함

약점:

- 복잡하다
- 기능이 많아 학습 비용이 높다

### OpenClaw

장점:

- 플랫폼/게이트웨이/권한/채널/디바이스 구조가 가장 강함
- 조직적 운용과 멀티채널 통합에 유리함
- 보안 모델이 매우 체계적임

약점:

- 개인이 바로 쓰기엔 무겁다
- 개념과 하위 시스템이 많아 초기 진입 비용이 큼

## 최종 한 문장

cclaw는 "Claude Code 기반 로컬 개인 비서", Hermes는 "도구와 기억이 풍부한 범용 에이전트 런타임", OpenClaw는 "멀티채널/멀티에이전트 AI 운영 플랫폼"이다.

## 참고한 소스

- Hermes docs home: https://hermes-agent.nousresearch.com/docs/
- Hermes repository: https://github.com/NousResearch/hermes-agent
- OpenClaw repository: https://github.com/openclaw/openclaw
- cclaw project context: `CLAUDE.md`, `pyproject.toml`, `src/cclaw/*`, `docs/*`
- Hermes cloned docs: `website/docs/user-guide/features/*`, `AGENTS.md`, `package.json`
- OpenClaw cloned docs: `docs/concepts/architecture.md`, `docs/concepts/delegate-architecture.md`, `README.md`, `package.json`, `AGENTS.md`
