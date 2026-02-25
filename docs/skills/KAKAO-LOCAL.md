# Kakao Local Skill Guide

A guide to installing and using the built-in Kakao Local skill for cclaw.

## Overview

The Kakao Local skill is a CLI-based skill that lets you search places, convert addresses, and look up coordinates through your Telegram bot.
It uses the [heg-wtf/kakao-cli](https://github.com/heg-wtf/kakao-cli) CLI tool.

### Key Features

- Address to coordinate conversion (geocoding)
- Coordinate to address conversion (reverse geocoding)
- Keyword place search with category filtering and radius search

## Prerequisites

### 1. Install kakao-cli

```bash
pip install git+https://github.com/heg-wtf/kakao-cli.git
```

Verify the installation:

```bash
kakao-cli --help
```

### 2. Kakao REST API Key

1. Open [Kakao Developers](https://developers.kakao.com)
2. Create an application
3. Copy the **REST API Key** from app settings

## Installation & Setup

### 1. Install the Built-in Skill

```bash
cclaw skills install kakao-local
```

### 2. Setup (Activate)

```bash
cclaw skills setup kakao-local
```

During setup, you'll be prompted to enter:
- `KAKAO_REST_API_KEY` — Your Kakao REST API key

### 3. Attach the Skill to a Bot

Via Telegram:
```
/skills attach kakao-local
```

### 4. Verify

```bash
cclaw skills
```

## Usage

After attaching the skill, send natural language requests via Telegram.

### Address Lookup

```
강남구 역삼동 좌표 알려줘
테헤란로 152 주소 검색해줘
서울시 강남구 위치 찾아줘
```

### Coordinate Lookup

```
127.028610, 37.499516 주소가 뭐야?
이 좌표의 주소 알려줘: 126.9707, 37.5547
```

### Place Search

```
강남역 근처 카페 찾아줘
현재 위치 반경 1km 약국 검색
판교역 주변 음식점 거리순으로
```

## How It Works

### allowed_tools

```yaml
allowed_tools:
  - "Bash(kakao-cli:*)"
  - "Bash(kakao:*)"
```

This allows all `kakao-cli` and `kakao` commands to run without permission prompts in Claude Code's `-p` mode.

### Environment Variable Injection

`KAKAO_REST_API_KEY` is stored during `cclaw skills setup` and injected into the Claude Code subprocess at runtime. The `kakao-cli` uses this for Kakao Local API authentication.

### Combining with Other Skills

The Kakao Local skill works well with:
- **naver-map**: Use coordinates from Kakao Local to generate Naver Map links
- **naver-search**: Search for places on Naver after finding locations via Kakao

## Troubleshooting

### kakao-cli command not found

```bash
which kakao-cli
# Should output a path
```

**Solution**: Install via `pip install git+https://github.com/heg-wtf/kakao-cli.git`.

### Authentication error

```
Error: 401 Unauthorized
```

**Solution**: Verify your REST API key at [Kakao Developers](https://developers.kakao.com/console/app), then re-run `cclaw skills setup kakao-local`.

### No results for keyword search

Kakao Local API may return empty results for queries without a specific location context.

**Solution**: Add location context with `--x`, `--y`, `--radius` options, or use more specific keywords.
