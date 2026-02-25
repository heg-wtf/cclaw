# DART Corporate Disclosure

금융감독원 전자공시시스템(DART) 공시 정보를 `dartcli`로 조회합니다. 기업 개황, 공시 목록, 재무정보, 공시 원문을 마크다운 형식으로 출력합니다.

## Prerequisites

- `dartcli` installed (`curl -fsSL https://raw.githubusercontent.com/seapy/dartcli/main/install.sh | sh`)
- DART OpenAPI 인증키 (https://opendart.fss.or.kr 에서 무료 발급)
- `DART_API_KEY` environment variable set during skill setup

## Available Commands

### search — 기업 검색

기업명이나 종목코드로 Corp Code를 조회합니다. 다른 명령에 입력할 정확한 이름을 확인할 때 사용합니다. API 키 없이 로컬 캐시만 사용합니다.

```bash
dartcli search 삼성
dartcli search 005930
```

### company — 기업 개황

대표이사, 설립일, 주소, 홈페이지 등 기업 기본 정보를 조회합니다.

```bash
dartcli company 삼성전자
dartcli company 005930
```

### list — 공시 목록

최근 공시 목록을 조회합니다. 출력된 접수번호를 `view` 명령에 사용합니다.

```bash
dartcli list 삼성전자
dartcli list 삼성전자 --type A --limit 5
dartcli list 삼성전자 --days 90
dartcli list 삼성전자 --start 20240101 --end 20241231
```

- `--type`: `A`(정기공시), `B`(주요사항보고), `C`(발행공시), `D`(지분공시), `E`(기타공시), `F`(외부감사관련)
- `--limit`: 조회 건수 (기본 20)
- `--days`: 최근 N일
- `--start`, `--end`: 조회 기간 (YYYYMMDD)

### finance — 재무정보

재무상태표, 손익계산서, 현금흐름표를 억원 단위로 조회합니다. 전기 대비 증감률도 함께 표시됩니다.

```bash
dartcli finance 삼성전자
dartcli finance 삼성전자 --year 2024
dartcli finance 삼성전자 --year 2024 --period half
dartcli finance 삼성전자 --year 2024 --type ofs
```

- `--year`: 사업연도 (기본: 작년)
- `--period`: `annual`(연간, 기본), `q1`(1분기), `half`(반기), `q3`(3분기)
- `--type`: `cfs`(연결, 기본), `ofs`(개별)

### view — 공시 원문 조회

`list`에서 확인한 접수번호로 공시 원문을 마크다운으로 출력합니다.

```bash
dartcli view 20251114002447
dartcli view 20251114002447 --browser
dartcli view 20251114002447 --download
dartcli view 20251114002447 --download -o ./report.zip
```

- `--browser`: DART 웹사이트에서 브라우저로 열기
- `--download`: ZIP 원문 파일로 저장

### cache — 캐시 관리

```bash
dartcli cache status
dartcli cache refresh
dartcli cache clear
```

## Global Options

- `--no-color`: 색상 출력 비활성화
- `--style <스타일>`: `auto`(기본), `dark`, `light`, `notty`

## Usage Guidelines

- 사용자가 기업 정보, 공시, 재무제표, 사업보고서 등을 물으면 이 스킬을 사용합니다.
- 동명 기업이 여럿일 수 있으므로 먼저 `dartcli search`로 정확한 기업명을 확인한 후 다른 명령을 실행합니다.
- 항상 `--no-color` 옵션을 붙여서 색상 코드 없이 깨끗한 텍스트를 받습니다.
- `view` 출력은 수천 줄 이상일 수 있으므로, 특정 섹션만 필요하면 `grep -A`로 필터링합니다.
- 재무정보 조회 시 연결재무제표(`cfs`)가 기본이며, 개별재무제표가 필요하면 `--type ofs`를 사용합니다.
- 한국어 기업명으로 직접 검색 가능합니다.
