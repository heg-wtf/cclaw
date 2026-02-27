# Naver Search

`naver-cli`로 네이버 검색 API 6종: local(장소), book, blog, cafe, news, shopping.

## Commands

```bash
naver-cli local search "강남역 맛집" [--display N] [--sort comment]        # sort: random(기본), comment
naver-cli book search "파이썬" [--display N] [--sort date|count]           # sort: sim(기본), date, count
naver-cli blog search "맛집 추천" [--display N] [--sort date]              # sort: sim(기본), date
naver-cli cafe search "여행 후기" [--display N] [--sort date]              # sort: sim(기본), date
naver-cli news search "경제" [--display N] [--sort date]                   # sort: sim(기본), date
naver-cli shopping search "노트북" [--display N] [--sort asc|dsc|date]     # sort: sim(기본), asc(저가), dsc(고가)
```

공통 옵션: `--display N` (결과 수), `--start N` (시작 위치), `--format text|markdown|json`

## Notes
- 간결한 결과: `--display 5` 기본 사용
- 채팅 출력: `--format markdown`, 파싱: `--format json`
- 장소/맛집 → `local`, 가격/상품 → `shopping`
- naver-map 스킬 가용 시 장소 결과에 지도 링크 결합
- 결과에 출처 링크 포함
- 한국어 검색어 인코딩 불필요
