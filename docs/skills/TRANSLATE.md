# Translate Skill Guide

A guide to installing and using the built-in Translate skill for cclaw.

## Overview

The Translate skill is a CLI-based skill that lets you translate text and transcripts through your Telegram bot.
It uses the [seapy/translatecli](https://github.com/seapy/translatecli) CLI tool powered by Google Gemini. It preserves the original format structure (Markdown, SRT, JSON, plain text).

### Key Features

- Plain text translation (inline, file, or stdin)
- sttcli transcript translation with format preservation
- Supports ISO language codes and natural language names
- Output to stdout or file

## Prerequisites

### 1. Install translatecli

```bash
uv tool install git+https://github.com/seapy/translatecli.git
```

Verify the installation:

```bash
translatecli --help
```

### 2. Gemini API Key

1. Open [Google AI Studio](https://aistudio.google.com/apikey)
2. Create an API key

## Installation & Setup

### 1. Install the Built-in Skill

```bash
cclaw skills install translate
```

### 2. Setup (Activate)

```bash
cclaw skills setup translate
```

During setup, you'll be prompted to enter:
- `GEMINI_API_KEY` — Your Gemini API key

### 3. Attach the Skill to a Bot

Via Telegram:
```
/skills attach translate
```

### 4. Verify

```bash
cclaw skills
```

## Usage

After attaching the skill, send natural language requests via Telegram.

### Text Translation

```
이 문장 영어로 번역해줘: 오늘 날씨가 좋습니다
Translate this to Japanese: The weather is nice today
이 내용 한국어로 번역해줘: Bonjour le monde
```

### File Translation

```
이 파일 한국어로 번역해줘 (attach a file)
transcript.md 파일을 일본어로 번역해줘
```

### Transcript Translation

```
이 sttcli 녹취록을 한국어로 번역해줘
이 SRT 자막 파일 영어로 번역해줘
```

## How It Works

### allowed_tools

```yaml
allowed_tools:
  - "Bash(translatecli:*)"
```

This allows all `translatecli` commands to run without permission prompts in Claude Code's `-p` mode.

### Environment Variable Injection

`GEMINI_API_KEY` is stored during `cclaw skills setup` and injected into the Claude Code subprocess at runtime. The `translatecli` uses this for Gemini API authentication.

## Troubleshooting

### translatecli command not found

```bash
which translatecli
# Should output a path
```

**Solution**: Install via `uv tool install git+https://github.com/seapy/translatecli.git`.

### Authentication error (Invalid API key)

```
Error: API key not valid
```

**Solution**: Verify your API key at [Google AI Studio](https://aistudio.google.com/apikey), then re-run `cclaw skills setup translate`.

### Garbled output for transcript formats

When translating sttcli output, make sure to use the `--sttcli` flag to preserve timestamps and speaker labels.

**Solution**: The bot's SKILL.md instructs it to use `--sttcli` automatically when transcript files are detected.
