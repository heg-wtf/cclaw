# DART Skill Guide

A guide to installing and using the built-in DART skill for cclaw.

## Overview

The DART skill is a CLI-based skill that lets you query Korean corporate disclosure data from the Financial Supervisory Service's DART system through your Telegram bot.
It uses the [seapy/dartcli](https://github.com/seapy/dartcli) CLI tool.

### Key Features

- Company search by name or stock code
- Company overview (CEO, address, homepage, etc.)
- Disclosure listing with type/date filtering
- Financial statements (balance sheet, income statement, cash flow) in KRW billions
- Full disclosure document viewing in Markdown

## Prerequisites

### 1. Install dartcli

```bash
curl -fsSL https://raw.githubusercontent.com/seapy/dartcli/main/install.sh | sh
```

Verify the installation:

```bash
dartcli version
```

### 2. DART OpenAPI Key

1. Open [DART OpenAPI](https://opendart.fss.or.kr/uss/umt/EgovMberInsertView.do)
2. Register an account (individual account is instant)
3. Issue an API key

## Installation & Setup

### 1. Install the Built-in Skill

```bash
cclaw skills install dart
```

### 2. Setup (Activate)

```bash
cclaw skills setup dart
```

During setup, you'll be prompted to enter:
- `DART_API_KEY` — Your DART OpenAPI key

### 3. Attach the Skill to a Bot

Via Telegram:
```
/skills attach dart
```

### 4. Verify

```bash
cclaw skills
```

## Usage

After attaching the skill, send natural language requests via Telegram.

### Company Information

```
삼성전자 기업 정보 알려줘
카카오 대표이사 누구야?
```

### Financial Statements

```
삼성전자 재무제표 보여줘
카카오 2024년 반기 재무정보
네이버 영업이익 추이 알려줘
```

### Disclosure Search

```
삼성전자 최근 공시 목록
카카오 정기공시 보여줘
LG에너지솔루션 사업보고서 찾아줘
```

### Disclosure Document

```
이 접수번호 공시 내용 보여줘: 20251114002447
사업보고서에서 사업 개요 부분만 요약해줘
```

## How It Works

### allowed_tools

```yaml
allowed_tools:
  - "Bash(dartcli:*)"
```

This allows all `dartcli` commands to run without permission prompts in Claude Code's `-p` mode.

### Environment Variable Injection

`DART_API_KEY` is stored during `cclaw skills setup` and injected into the Claude Code subprocess at runtime. The `dartcli` uses this for DART OpenAPI authentication.

## Troubleshooting

### dartcli command not found

```bash
which dartcli
# Should output a path like /usr/local/bin/dartcli
```

**Solution**: Install via `curl -fsSL https://raw.githubusercontent.com/seapy/dartcli/main/install.sh | sh`.

### Authentication error (Invalid API key)

```
Error: 인증키가 유효하지 않습니다
```

**Solution**: Verify your API key at [DART OpenAPI](https://opendart.fss.or.kr), then re-run `cclaw skills setup dart`.

### Multiple companies with same name

When `dartcli` finds multiple companies matching the query, it shows an interactive prompt. In agent mode this won't work.

**Solution**: Use `dartcli search <name>` first to find the exact company name or stock code, then use that for subsequent commands.
