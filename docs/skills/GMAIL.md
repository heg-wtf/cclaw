# Gmail Skill Guide

A guide to installing and using the built-in Gmail skill for cclaw.

## Overview

The Gmail skill is a CLI-based skill that lets you search, read, and send emails through your Telegram bot.
It uses the [steipete/gogcli](https://github.com/steipete/gogcli) (`gog`) CLI tool.

### Key Features

- Search emails with Gmail query syntax
- Read messages and threads
- Send emails, reply, forward
- Manage labels, drafts

## Prerequisites

### 1. Install gogcli

```bash
brew install steipete/tap/gogcli
```

Verify the installation:

```bash
gog --help
```

### 2. Google Cloud OAuth Setup

1. Open [Google Cloud Console](https://console.cloud.google.com/apis/credentials)
2. Create a project (or use existing)
3. Enable **Gmail API**: https://console.cloud.google.com/apis/api/gmail.googleapis.com
4. Configure **OAuth consent screen**: https://console.cloud.google.com/auth/branding
5. Create **OAuth client** (Desktop app type) and download the JSON file

### 3. Authorize Account

```bash
# Store OAuth credentials
gog auth credentials ~/Downloads/client_secret_....json

# Authorize your Google account
gog auth add you@gmail.com

# Test
export GOG_ACCOUNT=you@gmail.com
gog gmail labels list
```

## Installation & Setup

### 1. Install the Built-in Skill

```bash
cclaw skills install gmail
```

### 2. Setup (Activate)

```bash
cclaw skills setup gmail
```

During setup, you'll be prompted to enter your `GOG_ACCOUNT` (Google account email).
This is the same email you used with `gog auth add`.

### 3. Attach the Skill to a Bot

Via Telegram:
```
/skills attach gmail
```

### 4. Verify

```bash
cclaw skills
```

## Usage

After attaching the skill, send natural language requests via Telegram.

### Search Emails

```
Show me unread emails
Show emails from john@example.com
Find emails about "project deadline" from last week
```

### Read a Specific Email

```
Read the latest email from marketing
Show me the full thread about the budget report
```

### Send Email

```
Send an email to john@example.com with subject "Meeting Tomorrow" and body "Can we meet at 3pm?"
```

The bot will confirm recipient, subject, and body before sending.

### Reply to Email

```
Reply to the last email from John saying "Sounds good, see you then"
```

### Manage Labels

```
Label the last email as "Important"
Archive the email about the invoice
```

## How It Works

### allowed_tools

```yaml
allowed_tools:
  - "Bash(gog:*)"
```

This allows all `gog` commands to run without permission prompts in Claude Code's `-p` mode.

### Environment Variable Injection

The `GOG_ACCOUNT` environment variable is stored during `cclaw skills setup` and injected into the Claude Code subprocess at runtime. The `gog` CLI uses this to select which Google account to operate on.

### Safety Rules

SKILL.md includes guardrails:

- Always confirm before sending emails
- Never delete emails (use archive instead)
- Never modify filters or delegation settings without approval
- Confirm recipients when forwarding/replying

## Troubleshooting

### gog command not found

```bash
which gog
# Should output a path like /opt/homebrew/bin/gog
```

**Solution**: Install via `brew install steipete/tap/gogcli`.

### Authentication error

```
Error: no token for account
```

**Solution**: Run `gog auth add you@gmail.com` to authorize, then verify with `gog auth list`.

### Permission denied / insufficient scopes

```
Error: 403 insufficient scopes
```

**Solution**: Re-authorize with required scopes:
```bash
gog auth add you@gmail.com --services gmail --force-consent
```

### Bot waiting for permission

The bot says "Please approve in terminal":

**Solution**: Verify `Bash(gog:*)` is in `allowed_tools` in skill.yaml, then re-run `cclaw skills setup gmail`.
