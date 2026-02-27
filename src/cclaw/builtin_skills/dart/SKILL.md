# DART Corporate Disclosure

`dartcli`로 금융감독원 DART 공시 정보 조회. 기업 검색, 개황, 공시 목록, 재무정보, 공시 원문.

## Commands

```bash
# 기업 검색 (Corp Code 확인, API 키 불필요)
dartcli search 삼성
dartcli search 005930

# 기업 개황
dartcli company 삼성전자

# 공시 목록 (접수번호 → view 명령에 사용)
dartcli list 삼성전자 [--type A] [--limit 5] [--days 90] [--start 20240101 --end 20241231]
  --type: A(정기), B(주요사항), C(발행), D(지분), E(기타), F(외부감사)

# 재무정보 (억원 단위, 전기 대비 증감률 포함)
dartcli finance 삼성전자 [--year 2024] [--period annual|q1|half|q3] [--type cfs|ofs]
  기본: 작년, annual, cfs(연결)

# 공시 원문 조회
dartcli view <접수번호> [--browser] [--download [-o ./report.zip]]
```

## Notes
- 동명 기업 대비: 먼저 `dartcli search`로 정확한 기업명 확인
- 항상 `--no-color` 옵션 사용
- `view` 출력이 길면 `grep -A`로 특정 섹션 필터링
- 한국어 기업명 직접 검색 가능
