# Daiso

`daiso` CLI로 다이소몰 상품 검색.

## Commands

```bash
daiso search "약통" [--count N] [--page N] [--format text|markdown|json]
```

- `--count N` (`-c`): 결과 수 (1-100, 기본 30)
- `--page N` (`-p`): 페이지 번호 (기본 1)
- `--format` (`-f`): 출력 형식 (text, markdown, json)

## Examples

```bash
daiso search "텀블러" -c 5
daiso search "수납박스" -c 10 -f json
daiso search "접시" --page 2 --format markdown
```

## Notes

- 간결한 결과: `--count 5` 기본 사용
- 채팅 출력: `--format markdown`, 파싱/가공: `--format json`
- JSON 응답 필드: product_name, price, formatted_price, average_score, review_count, category, sold_out, detail_url
- 품절 상품은 sold_out 필드로 확인
- 상품 상세 링크 포함하여 안내
- 한국어 검색어 인코딩 불필요
- best-price 스킬 가용 시 다이소 검색 결과와 타 쇼핑몰 가격 비교 결합
