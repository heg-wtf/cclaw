# Naver Map

네이버 지도 웹 URL 생성. 모바일에서 앱 설치 시 앱으로 바로 열림. **반드시 Markdown 링크 형식으로 출력** (plain URL 금지).

## URLs

### Place Search (기본)
```
[강남역 지도](https://map.naver.com/p/search/강남역)
[홍대 카페](https://map.naver.com/p/search/홍대 카페)
```

### 좌표로 위치 표시
```
[정자동](https://map.naver.com/?lat=37.4979502&lng=127.0276368&title=정자동)
```

### 경로 안내 (좌표 필요, 모바일 웹)
```
https://m.map.naver.com/route.nhn?menu=route&sname={출발}&sx={경도}&sy={위도}&ename={도착}&ex={경도}&ey={위도}&pathType={mode}
```
pathType: 0=자동차, 1=대중교통(기본), 2=도보

### 좌표 없이 경로
```
[서울역에서 강남역](https://map.naver.com/p/search/서울역에서 강남역)
```

## Key Coordinates
서울역: 37.5547, 126.9707 / 강남역: 37.4981, 127.0276 / 홍대입구: 37.5573, 126.9255
여의도: 37.5219, 126.9245 / 잠실역: 37.5133, 127.1001

## Notes
- 장소명만 있으면 검색 URL(`/p/search/`) 사용, 좌표 불필요
- 이동수단 미지정 시 대중교통(pathType=1) 기본
- 한국어 파라미터 URL 인코딩 불필요
