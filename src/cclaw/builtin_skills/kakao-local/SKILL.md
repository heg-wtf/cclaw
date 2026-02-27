# Kakao Local

`kakao-cli`로 주소→좌표, 좌표→주소, 키워드 장소 검색.

## Commands

```bash
# 주소 → 좌표
kakao address search "강남구 역삼동" [--analyze-type exact] [--format json]

# 좌표 → 주소 (경도 위도 순서: x y)
kakao coordinate search 127.028610 37.499516 [--format markdown]

# 키워드 장소 검색
kakao keyword search "강남역 맛집" [--category CE7] [--sort distance] [--x 127.0 --y 37.5 --radius 1000] [--size 5] [--format json]
```

## Category Codes
MT1=대형마트, CS2=편의점, PS3=유치원, SC4=학교, AC5=학원, PK6=주차장, OL7=주유소, SW8=지하철, BK9=은행, CT1=문화시설, AG2=중개, PO3=공공기관, AT4=관광, AD5=숙박, FD6=음식점, CE7=카페, HP8=병원, PM9=약국

## Notes
- **좌표 순서: 경도(x) 먼저, 위도(y) 나중** — 일반적인 lat/lng 순서와 반대
- 근거리 검색: `--x`, `--y`, `--radius`, `--sort distance` 조합
- 채팅: `--format markdown`, 파싱: `--format json`
- naver-map 스킬 가용 시 반환 좌표로 지도 링크 생성
- 한국어 인코딩 불필요
