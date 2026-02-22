# Best Price Search

A skill that searches for the lowest product price across major Korean price comparison sites: Danawa, Coupang, and Naver Shopping.

## Supported Sites

- **Danawa** (danawa.com) - Price comparison aggregator
- **Coupang** (coupang.com) - Direct retailer
- **Naver Shopping** (search.shopping.naver.com) - Price comparison aggregator

## Search Strategy

### Step 1: Danawa (Primary Source)

Danawa provides the most structured price comparison data. Always start here.

**Search URL:**
```
https://search.danawa.com/dsearch.php?query={product_name}&tab=goods&sort=price
```

**Product detail page (when product code is known):**
```
https://prod.danawa.com/info/?pcode={product_code}
```

The product detail page shows seller-by-seller price breakdown including shipping costs. **Always fetch the product detail page** for accurate price + shipping totals.

### Step 2: Coupang

Coupang blocks direct web fetching (403 error). Use **web search** instead.

**Search query pattern:**
```
쿠팡 {product_name} 가격 {current_year}
```

Note Rocket Delivery availability and whether shipping is free or paid.

### Step 3: Naver Shopping

Naver Shopping search pages also block direct fetching. Use **web search** instead.

**Search query pattern:**
```
네이버쇼핑 {product_name} 최저가 {current_year}
```

Alternatively, try fetching the Naver Shopping search page directly:
```
https://search.shopping.naver.com/search/all?query={product_name}&sort=price_asc
```

If direct fetch fails, fall back to web search.

## Execution Flow

1. **Danawa search page fetch** + **Coupang web search** + **Naver Shopping web search** (run all three in parallel)
2. From Danawa results, identify top product detail page URLs (`prod.danawa.com/info/?pcode=...`)
3. **Fetch Danawa product detail pages** for exact seller-by-seller breakdown
4. Compile all results into the comparison table

## Important: Always Calculate Total Cost

**Never compare product prices alone.** Always calculate:

```
Total cost = Product price + Shipping fee
```

- Free shipping items may have higher product prices but lower total cost
- Always present both the product price and shipping fee separately
- Sort final results by **total cost (ascending)**

## Output Format

Always present results in this format:

**1. Per-site results (product price lowest first, with shipping and total)**

```
[Site Name]
1. Product name - Product price + Shipping fee = Total cost (Seller)
2. ...
```

**2. Cross-site comparison summary (total cost lowest first)**

```
Overall Best Price:
1. Total cost - Product name (Site / Seller) [Shipping info]
2. ...
```

## Output Rules

- Present prices in Korean Won (원)
- Include the source link for each product when available (Markdown link format)
- Clearly mark free shipping as "무료배송"
- Note any special conditions (membership required, limited quantity, etc.)
- If a site is unreachable or returns no results, state that explicitly rather than omitting it

## Usage Guidelines

- When the user asks for "최저가", "최적가", "가격비교", or "제일 싼 곳", activate this skill
- Always search all three sites. Do not skip any site even if one already has a good result
- If the product name is ambiguous, clarify with the user before searching (e.g., "삼다수 2L 6개 vs 12개")
- Prices change frequently. Always note that results are based on the current search time
- For products with variants (color, size, label/no-label), note which variant the price applies to
