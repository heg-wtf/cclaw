# Daiso Skill Guide

A guide to installing and using the built-in Daiso skill for cclaw.

## Overview

The Daiso skill is a CLI-based skill that lets you search products on Daiso Mall (Korea's largest discount store) through your Telegram bot.
It uses the [heg-wtf/daiso-cli](https://github.com/heg-wtf/daiso-cli) CLI tool.

### Key Features

- Product search by keyword
- Price, rating, review count display
- Category and sold-out status
- Direct product page links
- Multiple output formats (text, markdown, JSON)

## Prerequisites

### 1. Install daiso-cli

```bash
pip install git+https://github.com/heg-wtf/daiso-cli.git
```

Verify the installation:

```bash
daiso --help
```

## Installation & Setup

### 1. Install the Built-in Skill

```bash
cclaw skills install daiso
```

### 2. Setup (Activate)

```bash
cclaw skills setup daiso
```

No environment variables required. Setup checks that the `daiso` command is available.

### 3. Attach the Skill to a Bot

Via Telegram:
```
/skills attach daiso
```

### 4. Verify

```bash
cclaw skills
```

## Usage

After attaching the skill, send natural language requests via Telegram.

### Product Search

```
다이소에서 약통 검색해줘
다이소 텀블러 뭐 있어?
다이소몰에서 수납박스 찾아줘
```

### Price Check

```
다이소 접시 가격 알려줘
다이소에서 5000원 이하 노트 있어?
```

### Availability

```
다이소 스테인리스 텀블러 품절이야?
```

## How It Works

### allowed_tools

```yaml
allowed_tools:
  - "Bash(daiso:*)"
```

This allows all `daiso` commands to run without permission prompts in Claude Code's `-p` mode.

### No Environment Variables

Unlike other CLI skills, the Daiso skill requires no API keys or environment variables. The `daiso-cli` directly calls the Daiso Mall public search API.

## Troubleshooting

### daiso command not found

```bash
which daiso
# Should output a path like /usr/local/bin/daiso
```

**Solution**: Install via `pip install git+https://github.com/heg-wtf/daiso-cli.git`.

### No search results

```
검색 결과가 없습니다.
```

**Solution**: Try broader or different search terms. Daiso Mall search uses exact keyword matching.

### API error

```
API 오류 (status=500): 검색 요청 실패
```

**Solution**: Daiso Mall API may be temporarily unavailable. Retry after a few minutes.
