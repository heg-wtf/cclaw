# iMessage 스킬 가이드

cclaw의 빌트인 iMessage 스킬을 설치하고 사용하는 방법을 안내합니다.

## 개요

iMessage 스킬은 macOS의 iMessage/SMS를 Telegram 봇을 통해 읽고 보낼 수 있게 해주는 CLI 기반 스킬입니다.
[steipete/imsg](https://github.com/steipete/imsg) CLI 도구를 사용합니다.

### 주요 기능

- 최근 대화 목록 조회
- 특정 대화의 메시지 히스토리 조회
- 메시지/파일 발송
- 실시간 메시지 모니터링

## 사전 준비

### 1. imsg CLI 설치

[imsg GitHub Releases](https://github.com/steipete/imsg/releases)에서 macOS용 바이너리를 다운로드합니다.

```bash
# 예: ~/Downloads/imsg-macos/ 에 압축 해제된 경우
# 바이너리와 번들 파일 3개를 /usr/local/bin 에 복사
sudo cp ~/Downloads/imsg-macos/imsg /usr/local/bin/
sudo cp -R ~/Downloads/imsg-macos/PhoneNumberKit_PhoneNumberKit.bundle /usr/local/bin/
sudo cp -R ~/Downloads/imsg-macos/SQLite.swift_SQLite.bundle /usr/local/bin/
```

> `.bundle` 파일은 디렉토리이므로 반드시 `-R` 옵션을 사용해야 합니다.

설치 확인:

```bash
imsg --help
```

### 2. macOS 권한 설정

imsg가 메시지 데이터베이스에 접근하려면 **전체 디스크 접근 권한**이 필요합니다.

1. **시스템 설정** > **개인정보 보호 및 보안** > **전체 디스크 접근 권한**
2. 터미널 앱(Terminal.app, iTerm2 등)을 목록에 추가하고 활성화
3. cclaw를 데몬으로 실행하는 경우, `launchd`가 사용하는 셸도 권한 필요

> 권한이 없으면 `imsg chats` 실행 시 빈 결과가 나오거나 에러가 발생합니다.

## 스킬 설치 및 설정

### 1. 빌트인 스킬 설치

```bash
cclaw skills install imessage
```

이 명령은 `~/.cclaw/skills/imessage/` 디렉토리에 SKILL.md와 skill.yaml을 생성합니다.

### 2. 스킬 셋업 (활성화)

```bash
cclaw skills setup imessage
```

`imsg` 명령어가 PATH에 있는지 자동으로 확인합니다. 요구사항이 충족되면 스킬이 `active` 상태로 변경됩니다.

### 3. 봇에 스킬 연결

CLI에서:
```bash
# bot.yaml의 skills 목록에 추가됨
```

또는 Telegram에서:
```
/skills attach imessage
```

### 4. 연결 확인

```bash
cclaw skills
```

출력 예시:
```
✅ imessage (cli) ← my-bot
```

## 사용법

봇에 스킬을 연결한 후 Telegram에서 자연어로 요청합니다.

### 대화 목록 조회

```
최근 메시지 목록 보여줘
```

### 특정 사람 메시지 조회

```
임영선 메시지 보여줘
```

### 메시지 발송

```
임영선한테 "사람많아?" 보내줘
```

봇이 수신자와 내용을 확인한 후 발송 여부를 물어봅니다:

```
임영선(010-4944-7253)님에게 다음 메시지를 보내려고 합니다:
- 수신자: +821049447253
- 내용: "사람많아?"

보내도 될까요?
```

"응 보내"라고 답하면 발송됩니다.

> 세션 연속성 기능이 활성화되어 있어 대화 맥락이 유지됩니다.
> 첫 메시지에서 연락처를 조회하고, 다음 메시지에서 발송을 승인하는 멀티턴 흐름이 가능합니다.

## 동작 원리

### allowed_tools

skill.yaml에 정의된 `allowed_tools` 설정:

```yaml
allowed_tools:
  - "Bash(imsg:*)"
  - "Bash(watch:*)"
  - "Bash(osascript:*)"
```

이 설정은 Claude Code에 `--allowedTools` 플래그로 전달되어, 해당 명령을 권한 승인 없이 실행할 수 있게 합니다:

- `Bash(imsg:*)`: `imsg`로 시작하는 명령 (메시지 조회/발송)
- `Bash(watch:*)`: `watch`로 시작하는 명령 (실시간 모니터링용 시스템 `watch` 명령)
- `Bash(osascript:*)`: `osascript`로 시작하는 명령 (macOS 연락처 조회)

### 연락처 조회 (osascript)

이름으로 메시지를 요청하면 봇이 macOS 연락처(Contacts)에서 전화번호를 먼저 조회합니다:

```bash
osascript -e 'tell application "Contacts" to get {name, value of phones} of every person whose name contains "영선"'
```

- 부분 매칭 지원: "영선"으로 검색하면 "임영선"도 매칭됩니다
- 동명이인이 있을 경우 사용자에게 확인을 요청합니다
- 조회된 전화번호로 `imsg send --to` 명령을 실행합니다

**흐름 예시:**
1. "임영선한테 안녕 보내줘"
2. 봇이 `osascript`로 "영선" 또는 "임영선" 검색 → 전화번호 확인
3. 수신자/내용 확인 요청
4. 승인 후 `imsg send --to +8210XXXXXXXX --text "안녕"` 실행

### SKILL.md 지시사항

SKILL.md에는 Claude가 따라야 할 가이드라인이 포함됩니다:

- 메시지 발송 전 반드시 사용자 확인
- `--json` 옵션으로 구조화된 데이터 파싱
- 전화번호는 국제 형식 (`+821012345678`) 사용

### 세션 연속성

iMessage 스킬처럼 멀티턴 상호작용이 필요한 경우 세션 연속성이 중요합니다:

1. **첫 메시지**: `--session-id`로 새 Claude Code 세션 시작, conversation.md에서 이전 맥락 부트스트랩
2. **이후 메시지**: `--resume`으로 동일 세션 이어가기
3. **`/reset`**: 세션 ID 초기화, 새 세션 시작

## 문제 해결

### imsg 명령어를 찾을 수 없음

```
cclaw skills setup imessage
# Error: required command 'imsg' not found
```

**해결**: imsg 바이너리와 번들 파일을 `/usr/local/bin/`에 복사했는지 확인합니다.

```bash
which imsg
# /usr/local/bin/imsg 이 출력되어야 함
```

### 대화 목록이 비어있음

```
imsg chats
# (빈 결과)
```

**해결**: macOS 전체 디스크 접근 권한을 확인합니다.

### 메시지 발송이 안 됨 (권한 승인 대기)

봇이 "터미널에서 승인해주세요"라고 응답하는 경우:

**원인**: Claude Code가 `imsg send` 명령 실행 전 사용자 승인을 요구하지만, 봇은 비대화형 환경에서 실행되어 승인할 수 없습니다.

**해결**: skill.yaml의 `allowed_tools`에 `Bash(imsg:*)`가 포함되어 있는지 확인합니다.

```bash
cat ~/.cclaw/skills/imessage/skill.yaml
```

`allowed_tools` 항목이 있으면 `cclaw skills setup imessage`로 다시 활성화합니다.

### 맥락이 끊어짐 (멀티턴 실패)

"메시지 보여줘" → "이 번호로 보내줘" 흐름에서 봇이 맥락을 모르는 경우:

**해결**: `/reset` 후 다시 시도합니다. 세션 연속성이 자동으로 활성화됩니다.

### .bundle 파일 복사 시 Permission denied

```
cp: /usr/local/bin/imsg: Permission denied
```

**해결**: `sudo`를 사용합니다. `.bundle` 파일은 디렉토리이므로 `-R` 옵션이 필요합니다.

```bash
sudo cp ~/Downloads/imsg-macos/imsg /usr/local/bin/
sudo cp -R ~/Downloads/imsg-macos/PhoneNumberKit_PhoneNumberKit.bundle /usr/local/bin/
sudo cp -R ~/Downloads/imsg-macos/SQLite.swift_SQLite.bundle /usr/local/bin/
```
