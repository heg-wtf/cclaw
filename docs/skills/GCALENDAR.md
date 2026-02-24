# Google Calendar Skill Guide

A guide to installing and using the built-in Google Calendar skill for cclaw.

## Overview

The Google Calendar skill is a CLI-based skill that lets you view, create, and manage calendar events through your Telegram bot.
It uses the [steipete/gogcli](https://github.com/steipete/gogcli) (`gog`) CLI tool.

### Key Features

- View today's events and upcoming schedule
- Create and update events
- Check free/busy availability
- Detect scheduling conflicts
- RSVP to invitations

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
3. Enable **Google Calendar API**: https://console.cloud.google.com/apis/api/calendar-json.googleapis.com
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
gog calendar events --today
```

## Installation & Setup

### 1. Install the Built-in Skill

```bash
cclaw skills install gcalendar
```

### 2. Setup (Activate)

```bash
cclaw skills setup gcalendar
```

During setup, you'll be prompted to enter your `GOG_ACCOUNT` (Google account email).
This is the same email you used with `gog auth add`.

### 3. Attach the Skill to a Bot

Via Telegram:
```
/skills attach gcalendar
```

### 4. Verify

```bash
cclaw skills
```

## Usage

After attaching the skill, send natural language requests via Telegram.

### View Schedule

```
What's on my schedule today?
Show me this week's events
What do I have on Friday?
```

### Check Availability

```
Am I free at 3pm tomorrow?
Check if I have any conflicts next Monday afternoon
```

### Create Events

```
Create a meeting with John tomorrow at 2pm for 1 hour, title "Project Review"
Add a dentist appointment on March 5th at 10am
```

The bot will confirm date, time, title, and attendees before creating.

### Update Events

```
Move my 3pm meeting to 4pm
Change the location of tomorrow's standup to Room B
```

### RSVP

```
Accept the team dinner invitation
Decline the Friday meeting
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

### Shared Authentication with Gmail

Both Gmail and Calendar skills use the same `gog` CLI and `GOG_ACCOUNT`. If you've already set up the Gmail skill, the same OAuth credentials and account work for Calendar (as long as Calendar API is enabled and scopes are authorized).

### Safety Rules

SKILL.md includes guardrails:

- Always confirm before creating or modifying events
- Never delete events (suggest cancellation instead)
- Never accept/decline invitations without explicit approval
- Confirm attendee list when creating events with invitees

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

**Solution**: Re-authorize with Calendar scopes:
```bash
gog auth add you@gmail.com --services calendar --force-consent
```

### No events shown

```
gog calendar events --today
# (empty result)
```

**Solution**: Verify the correct account is selected (`gog auth list`) and Calendar API is enabled in Google Cloud Console.

### Bot waiting for permission

The bot says "Please approve in terminal":

**Solution**: Verify `Bash(gog:*)` is in `allowed_tools` in skill.yaml, then re-run `cclaw skills setup gcalendar`.
