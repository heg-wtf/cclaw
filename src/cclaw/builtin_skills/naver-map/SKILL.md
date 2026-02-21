# Naver Map

A skill that generates Naver Map web URLs for place search and route navigation links.
On mobile, if the Naver Maps app is installed, the app opens directly.

## Important: Link Output Rules

**Always output links in Markdown link format.** Never send URLs as plain text.

Correct example:
```
[Search Gangnam Station on Naver Map](https://map.naver.com/p/search/강남역)
```

Incorrect example (never do this):
```
https://map.naver.com/p/search/강남역
```

## URLs by Feature

### Place Search (Most Common)

Search by keyword without coordinates. **Use this as the default for place-related requests.**

```
https://map.naver.com/p/search/{query}
```

Examples:
- `[View Gangnam Station on map](https://map.naver.com/p/search/강남역)`
- `[Cafes near Hongdae](https://map.naver.com/p/search/홍대 카페)`
- `[Starbucks Yeoksam](https://map.naver.com/p/search/스타벅스 역삼점)`

### Show Place by Coordinates

Display a specific location on the map when coordinates are known.

```
https://map.naver.com/?lat={latitude}&lng={longitude}&title={place_name}
```

Example:
- `[View Jeongja-dong](https://map.naver.com/?lat=37.4979502&lng=127.0276368&title=정자동)`

### Route Navigation (Mobile Web)

Directions between origin and destination. Requires coordinates.

```
https://m.map.naver.com/route.nhn?menu=route&sname={origin_name}&sx={origin_longitude}&sy={origin_latitude}&ename={destination_name}&ex={destination_longitude}&ey={destination_latitude}&pathType={transport_mode}
```

pathType values:
- 0: Car
- 1: Public transit
- 2: Walking

Example:
- `[View public transit route](https://m.map.naver.com/route.nhn?menu=route&sname=서울대학교&sx=126.9522394&sy=37.4640070&ename=올림픽공원&ex=127.1230074&ey=37.5209436&pathType=1)`

### Route Navigation (Without Coordinates)

When coordinates are unknown, **provide two search links**:

```
Origin: [Search Seoul Station](https://map.naver.com/p/search/서울역)
Destination: [Search Gangnam Station](https://map.naver.com/p/search/강남역)
```

Or **combine origin and destination in a single search**:

```
[Directions from Seoul Station to Gangnam Station](https://map.naver.com/p/search/서울역에서 강남역)
```

## Key Coordinate Reference

Seoul Station: lat=37.5547, lng=126.9707
Gangnam Station: lat=37.4981, lng=127.0276
Hongdae Entrance: lat=37.5573, lng=126.9255
Yeouido: lat=37.5219, lng=126.9245
Jamsil Station: lat=37.5133, lng=127.1001

## Usage Guidelines

- For place names only, use **search URL** (`/p/search/`). No coordinates needed.
- Only use route navigation URLs when coordinates are known.
- Default to **public transit** (pathType=1) when transport mode is not specified.
- Korean parameters can be used as-is without URL encoding.
- Write link text that is easy for users to understand (e.g., "View on Naver Map", "View public transit route").
