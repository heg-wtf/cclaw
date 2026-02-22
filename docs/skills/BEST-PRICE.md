# Best Price Skill Guide

A skill that searches for the lowest product price across major Korean price comparison sites: Danawa, Coupang, and Naver Shopping.

## Installation

```bash
cclaw skills install best-price
```

## Usage

Attach the skill in Telegram and ask for price comparisons.

```
/skills attach best-price
삼다수 2L 12개 최저가 찾아줘
에어팟 프로 2 가격비교 해줘
다이슨 V15 제일 싼 곳 알려줘
```

The bot searches all three sites and presents a comparison table with total costs (product price + shipping).

## Supported Sites

- **Danawa** (danawa.com) — Price comparison aggregator, primary data source
- **Coupang** (coupang.com) — Direct retailer (searched via web search due to access restrictions)
- **Naver Shopping** (search.shopping.naver.com) — Price comparison aggregator (searched via web search due to access restrictions)

## Skill Type

`knowledge` — No CLI tools or external dependencies required. Uses web fetching and web search capabilities already available in Claude Code.

## How It Works

1. **Danawa**: Fetches search results and product detail pages directly for seller-by-seller price breakdown
2. **Coupang**: Uses web search (direct page access returns 403)
3. **Naver Shopping**: Uses web search (direct page access is blocked)
4. All three sites are searched **in parallel** for speed
5. Results are sorted by **total cost** (product price + shipping fee), not product price alone

## Technical Notes

- Coupang and Naver Shopping block direct web fetching, so the skill instructs Claude to fall back to web search for those sites
- Danawa product detail pages (`prod.danawa.com/info/?pcode=...`) provide the most accurate price + shipping data
- Prices are real-time and may change between search and purchase
- Free shipping items may appear more expensive by product price but cheaper in total cost
