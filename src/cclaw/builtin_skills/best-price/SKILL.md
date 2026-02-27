# Best Price Search

한국 3대 가격비교 사이트(다나와, 쿠팡, 네이버쇼핑)에서 최저가 검색. **총비용 = 상품가 + 배송비** 기준 비교.

## Search Strategy

3개 사이트 병렬 검색:

**다나와** (Primary): `https://search.danawa.com/dsearch.php?query={상품명}&tab=goods&sort=price`
- 상세 페이지 `https://prod.danawa.com/info/?pcode={code}` 에서 판매처별 가격+배송비 확인 (반드시 fetch)

**Coupang (쿠팡)**: 직접 fetch 차단(403). 웹 검색 사용 → `쿠팡 {상품명} 가격 {현재연도}`

**네이버쇼핑**: 웹 검색 사용 → `네이버쇼핑 {상품명} 최저가 {현재연도}`
- 또는 `https://search.shopping.naver.com/search/all?query={상품명}&sort=price_asc` 시도, 실패 시 웹 검색 fallback

## Execution Flow
1. 다나와 검색 + 쿠팡 웹 검색 + 네이버쇼핑 웹 검색 (병렬)
2. 다나와 상세 페이지 fetch (판매처별 가격+배송비)
3. 결과 종합

## Output Format

사이트별 결과 (상품가 낮은 순, 배송비·총비용 포함) → 전체 최저가 순위 (총비용 오름차순)

- 가격: 원 단위, 무료배송은 "무료배송" 표기
- 출처 링크 Markdown 형식
- 사이트 접속 불가/결과 없음 시 명시
- 상품 모호 시 사용자에게 확인 (예: "삼다수 2L 6개 vs 12개")
- 옵션(색상, 사이즈) 해당 여부 표기
