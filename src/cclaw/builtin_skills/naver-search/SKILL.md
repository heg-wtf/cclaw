# Naver Search

Naver Open API search via `naver-cli`. Supports 6 search types: local (places), book, blog, cafe, news, shopping.

## Prerequisites

- `naver-cli` installed (`pip install git+https://github.com/heg-wtf/naver-cli.git`)
- Naver Developer Center (https://developers.naver.com) app registered
- `NAVER_CLIENT_ID` and `NAVER_CLIENT_SECRET` environment variables set during skill setup

## Available Commands

### Local (Place) Search

```bash
naver-cli local search "강남역 맛집"
naver-cli local search "판교 카페" --display 3 --sort comment
```

- `--sort`: `random` (accuracy, default), `comment` (review count)

### Book Search

```bash
naver-cli book search "파이썬"
naver-cli book search "파이썬" --display 20 --sort date
```

- `--sort`: `sim` (accuracy, default), `date` (publish date), `count` (sales)

### Blog Search

```bash
naver-cli blog search "맛집 추천"
naver-cli blog search "맛집 추천" --sort date
```

- `--sort`: `sim` (accuracy, default), `date` (date)

### Cafe Article Search

```bash
naver-cli cafe search "여행 후기"
naver-cli cafe search "여행 후기" --display 15
```

- `--sort`: `sim` (accuracy, default), `date` (date)

### News Search

```bash
naver-cli news search "경제"
naver-cli news search "경제" --sort date --display 20
```

- `--sort`: `sim` (accuracy, default), `date` (date)

### Shopping Search

```bash
naver-cli shopping search "노트북"
naver-cli shopping search "노트북" --sort asc
```

- `--sort`: `sim` (accuracy, default), `date` (date), `asc` (price low-to-high), `dsc` (price high-to-low)

## Common Options

| Option | Description | Default |
|--------|-------------|---------|
| `--display` | Number of results | varies by type |
| `--start` | Result start position | 1 |
| `--sort` | Sort order | varies by type |
| `--format` | Output format (`text`, `markdown`, `json`) | text |

## Output Format Guidelines

- Use `--format markdown` when you need to present results to the user in chat (most readable in Telegram).
- Use `--format json` when you need to parse or filter results programmatically.
- Use `--format text` (default) for general display.

## Usage Guidelines

- When the user asks to "search Naver" or asks about local places, restaurants, books, news, blog posts, cafe articles, or product shopping, use the appropriate search type.
- For place/restaurant searches, use `local search`. For price/product searches, use `shopping search`.
- Default to `--display 5` for concise results. Use larger values only when the user requests more.
- For place search results, consider combining with the naver-map skill (if available) to provide map links.
- Present results in a clean, readable format. Summarize key information (name, address, category for local; title, author, price for books; title, price, seller for shopping).
- Always include the source link when available in search results.
- Korean search queries work as-is without encoding.
