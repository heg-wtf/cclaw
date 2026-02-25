# Naver Search Skill Guide

A guide to installing and using the built-in Naver Search skill for cclaw.

## Overview

The Naver Search skill is a CLI-based skill that lets you search Naver's 6 search APIs through your Telegram bot.
It uses the [heg-wtf/naver-cli](https://github.com/heg-wtf/naver-cli) CLI tool.

### Key Features

- Local (place) search with review-based sorting
- Book search with sales/date sorting
- Blog, Cafe article, News search
- Shopping search with price sorting
- Multiple output formats (text, markdown, json)

## Prerequisites

### 1. Install naver-cli

```bash
pip install git+https://github.com/heg-wtf/naver-cli.git
```

Verify the installation:

```bash
naver-cli --help
```

### 2. Naver Developer API Key

1. Open [Naver Developer Center](https://developers.naver.com)
2. Register an application
3. Enable **Search** API
4. Copy **Client ID** and **Client Secret**

## Installation & Setup

### 1. Install the Built-in Skill

```bash
cclaw skills install naver-search
```

### 2. Setup (Activate)

```bash
cclaw skills setup naver-search
```

During setup, you'll be prompted to enter:
- `NAVER_CLIENT_ID` — Your Naver API Client ID
- `NAVER_CLIENT_SECRET` — Your Naver API Client Secret

### 3. Attach the Skill to a Bot

Via Telegram:
```
/skills attach naver-search
```

### 4. Verify

```bash
cclaw skills
```

## Usage

After attaching the skill, send natural language requests via Telegram.

### Place Search

```
강남역 근처 맛집 찾아줘
판교 카페 추천해줘
홍대 맛집 리뷰 많은 순으로 보여줘
```

### Book Search

```
파이썬 관련 책 추천해줘
최근 나온 경제 도서 알려줘
```

### Blog Search

```
제주도 여행 블로그 찾아줘
맛집 추천 블로그 최신순으로
```

### News Search

```
오늘 경제 뉴스 보여줘
AI 관련 최신 뉴스
```

### Shopping Search

```
노트북 최저가 검색해줘
에어팟 가격 낮은순으로 보여줘
```

## How It Works

### allowed_tools

```yaml
allowed_tools:
  - "Bash(naver-cli:*)"
  - "Bash(naver:*)"
```

This allows all `naver-cli` and `naver` commands to run without permission prompts in Claude Code's `-p` mode.

### Environment Variable Injection

`NAVER_CLIENT_ID` and `NAVER_CLIENT_SECRET` are stored during `cclaw skills setup` and injected into the Claude Code subprocess at runtime. The `naver-cli` uses these for Naver Open API authentication.

## Troubleshooting

### naver-cli command not found

```bash
which naver-cli
# Should output a path
```

**Solution**: Install via `pip install git+https://github.com/heg-wtf/naver-cli.git`.

### Authentication error (Invalid API key)

```
Error: 401 Unauthorized
```

**Solution**: Verify your API keys at [Naver Developer Center](https://developers.naver.com/apps), then re-run `cclaw skills setup naver-search`.

### No search results

Naver Search API may return empty results for very specific queries.

**Solution**: Try broader search terms or different search types.
