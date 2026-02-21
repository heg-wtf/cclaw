# iMessage Skill Guide

A guide to installing and using the built-in iMessage skill for cclaw.

## Overview

The iMessage skill is a CLI-based skill that lets you read and send iMessage/SMS through your Telegram bot on macOS.
It uses the [steipete/imsg](https://github.com/steipete/imsg) CLI tool.

### Key Features

- View recent conversation list
- Read message history for a specific conversation
- Send messages and files
- Real-time message monitoring

## Prerequisites

### 1. Install imsg CLI

Download the macOS binary from [imsg GitHub Releases](https://github.com/steipete/imsg/releases).

```bash
# Example: if extracted to ~/Downloads/imsg-macos/
# Copy the binary and bundle files to /usr/local/bin
sudo cp ~/Downloads/imsg-macos/imsg /usr/local/bin/
sudo cp -R ~/Downloads/imsg-macos/PhoneNumberKit_PhoneNumberKit.bundle /usr/local/bin/
sudo cp -R ~/Downloads/imsg-macos/SQLite.swift_SQLite.bundle /usr/local/bin/
```

> `.bundle` files are directories, so the `-R` flag is required.

Verify the installation:

```bash
imsg --help
```

### 2. macOS Permissions

imsg requires **Full Disk Access** to read the message database.

1. Open **System Settings** > **Privacy & Security** > **Full Disk Access**
2. Add your terminal app (Terminal.app, iTerm2, etc.) and enable it
3. If running cclaw as a daemon, the shell used by `launchd` also needs permission

> Without permission, `imsg chats` will return empty results or errors.

## Installation & Setup

### 1. Install the Built-in Skill

```bash
cclaw skills install imessage
```

This creates `SKILL.md` and `skill.yaml` in `~/.cclaw/skills/imessage/`.

### 2. Setup (Activate)

```bash
cclaw skills setup imessage
```

This automatically checks if `imsg` is available in your PATH. If requirements are met, the skill status changes to `active`.

### 3. Attach the Skill to a Bot

Via CLI:
```bash
# Adds to the skills list in bot.yaml
```

Or via Telegram:
```
/skills attach imessage
```

### 4. Verify

```bash
cclaw skills
```

Expected output:
```
imessage (cli) <- my-bot
```

## Usage

After attaching the skill to a bot, send natural language requests via Telegram.

### View Recent Conversations

```
Show me recent messages
```

### Read Messages from a Specific Person

```
Show me messages from John
```

### Send a Message

```
Send "Are you there?" to John
```

The bot will confirm the recipient and content before sending:

```
I'm about to send the following message to John Smith (010-1234-5678):
- Recipient: +821012345678
- Content: "Are you there?"

Shall I send it?
```

Reply "Yes" to proceed.

> Session continuity keeps conversation context across messages.
> Multi-turn flows like looking up a contact first, then approving the send, work seamlessly.

## How It Works

### allowed_tools

The `allowed_tools` configuration in skill.yaml:

```yaml
allowed_tools:
  - "Bash(imsg:*)"
  - "Bash(watch:*)"
  - "Bash(osascript:*)"
```

These are passed to Claude Code via the `--allowedTools` flag, allowing these commands to run without permission prompts:

- `Bash(imsg:*)`: Commands starting with `imsg` (message read/send)
- `Bash(watch:*)`: Commands starting with `watch` (real-time monitoring via system `watch`)
- `Bash(osascript:*)`: Commands starting with `osascript` (macOS Contacts lookup)

### Contacts Lookup (osascript)

When you request a message by name, the bot first looks up the phone number from macOS Contacts:

```bash
osascript -e 'tell application "Contacts" to get {name, value of phones} of every person whose name contains "John"'
```

- Partial matching supported: searching "John" matches "John Smith"
- If multiple matches are found, the bot asks you to clarify
- The resolved phone number is used with `imsg send --to`

**Example flow:**
1. "Send hello to John"
2. Bot runs `osascript` to search "John" -> finds phone number
3. Bot asks for confirmation of recipient and content
4. After approval, runs `imsg send --to +821012345678 --text "hello"`

### SKILL.md Instructions

SKILL.md contains guidelines for Claude to follow:

- Always confirm with the user before sending messages
- Use `--json` option for structured data parsing
- Use international format for phone numbers (`+821012345678`)

### Session Continuity

Session continuity is essential for multi-turn interactions like iMessage:

1. **First message**: Starts a new Claude Code session with `--session-id`, bootstrapping recent context from conversation.md
2. **Subsequent messages**: Continues the same session with `--resume`
3. **`/reset`**: Clears session ID, starts a fresh session

## Troubleshooting

### imsg command not found

```
cclaw skills setup imessage
# Error: required command 'imsg' not found
```

**Solution**: Verify that the imsg binary and bundle files are copied to `/usr/local/bin/`.

```bash
which imsg
# Should output: /usr/local/bin/imsg
```

### Empty conversation list

```
imsg chats
# (empty result)
```

**Solution**: Check macOS Full Disk Access permissions.

### Message sending fails (waiting for permission)

The bot responds with "Please approve in terminal":

**Cause**: Claude Code requires user approval before running `imsg send`, but the bot runs in a non-interactive environment where approval isn't possible.

**Solution**: Verify that `Bash(imsg:*)` is included in `allowed_tools` in skill.yaml.

```bash
cat ~/.cclaw/skills/imessage/skill.yaml
```

If `allowed_tools` is present, re-activate with `cclaw skills setup imessage`.

### Context lost (multi-turn failure)

"Show messages" -> "Send to this number" flow fails because the bot loses context:

**Solution**: Run `/reset` and try again. Session continuity will activate automatically.

### Permission denied when copying .bundle files

```
cp: /usr/local/bin/imsg: Permission denied
```

**Solution**: Use `sudo`. `.bundle` files are directories, so the `-R` flag is required.

```bash
sudo cp ~/Downloads/imsg-macos/imsg /usr/local/bin/
sudo cp -R ~/Downloads/imsg-macos/PhoneNumberKit_PhoneNumberKit.bundle /usr/local/bin/
sudo cp -R ~/Downloads/imsg-macos/SQLite.swift_SQLite.bundle /usr/local/bin/
```
