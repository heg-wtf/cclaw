# Kakao Local

Kakao Local API via `kakao-cli`. Address-to-coordinate conversion, coordinate-to-address conversion, and keyword place search.

## Prerequisites

- `kakao-cli` installed (`pip install git+https://github.com/heg-wtf/kakao-cli.git`)
- Kakao Developer (https://developers.kakao.com) REST API key issued
- `KAKAO_REST_API_KEY` environment variable set during skill setup

## Available Commands

### Address to Coordinate

Convert an address string to latitude/longitude coordinates.

```bash
kakao address search "강남구 역삼동"
kakao address search "테헤란로 152" --analyze-type exact
kakao address search "서울시 강남구" --format json
```

- `--analyze-type`: `similar` (default), `exact` (exact match only)

### Coordinate to Address

Convert latitude/longitude coordinates to an address.

```bash
kakao coordinate search 127.028610 37.499516
kakao coordinate search 127.028610 37.499516 --format markdown
```

- Arguments: `<longitude> <latitude>` (x, y order)

### Keyword Place Search

Search places by keyword. Supports category filtering and location-based radius search.

```bash
kakao keyword search "강남역 맛집"
kakao keyword search "카페" --category CE7 --sort distance --x 127.0 --y 37.5 --radius 1000
kakao keyword search "약국" --format json --size 5
```

- `--category`: Category group code (see Category Codes below)
- `--sort`: `accuracy` (default), `distance` (requires x, y)
- `--x`, `--y`: Center longitude/latitude for radius search
- `--radius`: Search radius in meters (0-20000)
- `--size`: Number of results (1-15, default: 15)

## Category Group Codes

| Code | Category |
|------|----------|
| MT1 | Large mart |
| CS2 | Convenience store |
| PS3 | Kindergarten |
| SC4 | School |
| AC5 | Academy |
| PK6 | Parking lot |
| OL7 | Gas station |
| SW8 | Subway station |
| BK9 | Bank |
| CT1 | Cultural facility |
| AG2 | Brokerage |
| PO3 | Public institution |
| AT4 | Tourist attraction |
| AD5 | Accommodation |
| FD6 | Restaurant |
| CE7 | Cafe |
| HP8 | Hospital |
| PM9 | Pharmacy |

## Common Options

| Option | Description | Default |
|--------|-------------|---------|
| `--format` | Output format (`text`, `markdown`, `json`) | text |
| `--size` | Number of results (keyword search) | 15 |
| `--page` | Result page number | 1 |

## Usage Guidelines

- When the user asks about addresses, coordinates, or place searches in Korea, use this skill.
- For place/restaurant/cafe searches, use `keyword search`. For address lookups, use `address search`.
- Use `--format markdown` for chat-friendly results. Use `--format json` when parsing is needed.
- For proximity-based searches, combine `--x`, `--y`, `--radius`, and `--sort distance` for best results.
- Coordinate order is **longitude first, latitude second** (x, y) — this differs from the common lat/lng convention.
- For place search results, consider combining with the naver-map skill (if available) to provide map links using the returned coordinates.
- Present results clearly: place name, address, category, phone number, and distance (when available).
- Korean search queries work as-is without encoding.
