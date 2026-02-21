```
  ██████╗ ██████╗██╗      █████╗ ██╗    ██╗
 ██╔════╝██╔════╝██║     ██╔══██╗██║    ██║
 ██║     ██║     ██║     ███████║██║ █╗ ██║
 ██║     ██║     ██║     ██╔══██║██║███╗██║
 ╚██████╗╚██████╗███████╗██║  ██║╚███╔███╔╝
  ╚═════╝ ╚═════╝╚══════╝╚═╝  ╚═╝ ╚══╝╚══╝
```

# cclaw (claude-claw)

> [한국어](README.ko.md)

Personal AI assistant powered by Telegram + Claude Code.
A multi-bot, file-based session system that runs locally on Mac (Intel/Apple Silicon).

## Table of Contents

- [Design Principles](#design-principles)
- [Requirements](#requirements)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Skills](#skills)
  - [iMessage](#imessage)
  - [Apple Reminders](#apple-reminders)
- [Telegram Commands](#telegram-commands)
- [File Handling](#file-handling)
- [Tech Stack](#tech-stack)
- [CLI Commands](#cli-commands)
- [Project Structure](#project-structure)
- [Runtime Data](#runtime-data)
- [Documentation](#documentation)
- [Testing](#testing)
- [License](#license)

## Design Principles

- **Local First**: No server required. Long Polling. No SSL or public IP needed.
- **File Based**: No database. Session = directory. Conversation = markdown.
- **Claude Code Delegation**: No direct LLM API calls. Runs `claude -p` as a subprocess.
- **CLI First**: Everything from onboarding to bot management is done in the terminal.

## Requirements

- Python >= 3.11
- Node.js (Claude Code runtime)
- [Claude Code CLI](https://www.npmjs.com/package/@anthropic-ai/claude-code)
- [uv](https://docs.astral.sh/uv/)

## Installation

### uv (Recommended)

```bash
uv sync
```

### pip / pipx

```bash
pip install .
# or
pipx install .
```

## Quick Start

```bash
# Check environment
cclaw doctor                    # pip/pipx install
uv run cclaw doctor             # uv

# Initial setup (Telegram bot token required)
cclaw init

# Bot management
cclaw bot list
cclaw bot add
cclaw bot remove <name>

# Run bots
cclaw start              # Foreground
cclaw start --daemon     # Background (launchd)
cclaw stop               # Stop daemon
cclaw status             # Show running status
```

## Skills

cclaw has a **skill system** that extends your bot's capabilities with tools and knowledge. Skills are modular — attach or detach them per bot as needed.

- **Markdown skills**: Just a `SKILL.md` file. Adds instructions/knowledge to the bot.
- **Tool-based skills**: Include `skill.yaml` with CLI tools, MCP servers, or browser automation.
- **Built-in skills**: Pre-packaged skill templates installable with `cclaw skills install <name>`.

### iMessage

Read and send iMessage/SMS through your Telegram bot using the [imsg](https://github.com/steipete/imsg) CLI.

```bash
cclaw skills install imessage
cclaw skills setup imessage
```

Then in Telegram:
```
/skills attach imessage
Show me recent messages
Send "hello" to John
```

See the full guide: [iMessage Skill Guide](docs/skills/IMESSAGE.md)

### Apple Reminders

Manage macOS Reminders through your Telegram bot using the [reminders-cli](https://github.com/keith/reminders-cli).

```bash
brew install keith/formulae/reminders-cli
cclaw skills install reminders
cclaw skills setup reminders
```

Then in Telegram:
```
/skills attach reminders
What do I need to do today?
Add "Buy groceries" to Shopping list for tomorrow
```

See the full guide: [Apple Reminders Skill Guide](docs/skills/REMINDERS.md)

## Telegram Commands

| Command | Description |
|---------|-------------|
| `/start` | Bot introduction |
| `/reset` | Clear conversation (keep workspace) |
| `/resetall` | Delete entire session |
| `/files` | List workspace files |
| `/send <filename>` | Send workspace file |
| `/status` | Session status |
| `/model` | Show current model (with version) |
| `/model <name>` | Change model (sonnet/opus/haiku) |
| `/streaming` | Show streaming status |
| `/streaming on/off` | Toggle streaming mode |
| `/memory` | Show bot memory |
| `/memory clear` | Clear bot memory |
| `/skills` | List all skills (installed + available builtins) |
| `/skills attach <name>` | Attach a skill |
| `/skills detach <name>` | Detach a skill |
| `/cron list` | List cron jobs |
| `/cron run <name>` | Run a cron job now |
| `/heartbeat` | Heartbeat status |
| `/heartbeat on` | Enable heartbeat |
| `/heartbeat off` | Disable heartbeat |
| `/heartbeat run` | Run heartbeat now |
| `/cancel` | Stop running process |
| `/version` | Version info |
| `/help` | Show commands |

## File Handling

Send photos or documents to the bot and they are automatically saved to the workspace and forwarded to Claude Code.
If a caption is included, it is used as the prompt.
Use the `/send` command to retrieve workspace files back via Telegram.

---

## Tech Stack

| Component | Choice |
|-----------|--------|
| Package Manager | uv |
| CLI | Typer + Rich |
| Telegram | python-telegram-bot v21+ |
| Configuration | PyYAML |
| Cron Scheduler | croniter |
| AI Engine | Claude Code CLI (`claude -p`, streaming) |
| Process Manager | launchd (macOS) |

## CLI Commands

```bash
# Banner
cclaw                          # Show ASCII art banner

# Onboarding
cclaw init                     # Initial setup
cclaw doctor                   # Environment check

# Bot management
cclaw bot list                 # List bots (with model info)
cclaw bot add                  # Add a bot
cclaw bot remove <name>        # Remove a bot
cclaw bot edit <name>          # Edit bot.yaml
cclaw bot model <name>         # Show current model
cclaw bot model <name> opus    # Change model
cclaw bot streaming <name>     # Show streaming status
cclaw bot streaming <name> off # Toggle streaming on/off

# Skill management
cclaw skills                   # List all skills (installed + available builtins)
cclaw skills add               # Create a skill interactively
cclaw skills remove <name>     # Remove a skill
cclaw skills setup <name>      # Setup skill (check requirements, activate)
cclaw skills test <name>       # Test skill requirements
cclaw skills edit <name>       # Edit SKILL.md ($EDITOR)
cclaw skills builtins          # List available built-in skills
cclaw skills install           # List available built-in skills
cclaw skills install <name>    # Install a built-in skill

# Cron job management
cclaw cron list <bot>          # List cron jobs
cclaw cron add <bot>           # Add a cron job interactively
cclaw cron remove <bot> <job>  # Remove a cron job
cclaw cron enable <bot> <job>  # Enable a cron job
cclaw cron disable <bot> <job> # Disable a cron job
cclaw cron run <bot> <job>     # Run a cron job immediately (test)

# Memory management
cclaw memory show <bot>        # Show memory contents
cclaw memory edit <bot>        # Edit MEMORY.md ($EDITOR)
cclaw memory clear <bot>       # Clear memory

# Heartbeat management
cclaw heartbeat status         # Show heartbeat status for all bots
cclaw heartbeat enable <bot>   # Enable heartbeat
cclaw heartbeat disable <bot>  # Disable heartbeat
cclaw heartbeat run <bot>      # Run heartbeat immediately (test)
cclaw heartbeat edit <bot>     # Edit HEARTBEAT.md ($EDITOR)

# Run
cclaw start                    # Foreground
cclaw start --daemon           # Background (launchd)
cclaw stop                     # Stop daemon
cclaw status                   # Show status

# Logs
cclaw logs                     # Show today's log
cclaw logs -f                  # Tail mode
cclaw logs clean               # Delete logs older than 7 days
cclaw logs clean -d 30         # Keep last 30 days
cclaw logs clean --dry-run     # Preview without deleting
```

## Project Structure

```
cclaw/
├── pyproject.toml
├── src/cclaw/
│   ├── cli.py              # Typer CLI entry point (ASCII art banner)
│   ├── config.py           # Configuration load/save
│   ├── onboarding.py       # Setup wizard
│   ├── claude_runner.py    # Claude Code subprocess runner (batch + streaming)
│   ├── session.py          # Session directory management
│   ├── handlers.py         # Telegram handler factory
│   ├── bot_manager.py      # Multi-bot lifecycle
│   ├── skill.py            # Skill management (create/attach/install/MCP/CLAUDE.md composition)
│   ├── builtin_skills/     # Built-in skill templates (imessage, reminders, ...)
│   │   ├── __init__.py     # Built-in skill registry
│   │   ├── imessage/       # iMessage skill (imsg CLI)
│   │   └── reminders/      # Apple Reminders skill (reminders-cli)
│   ├── cron.py             # Cron schedule automation
│   ├── heartbeat.py        # Heartbeat (periodic situation awareness)
│   └── utils.py            # Utilities
└── tests/
```

## Runtime Data

Configuration and session data are stored in `~/.cclaw/`. Override the path with the `CCLAW_HOME` environment variable.

```
~/.cclaw/
├── config.yaml
├── bots/
│   └── <bot-name>/
│       ├── bot.yaml
│       ├── CLAUDE.md
│       ├── MEMORY.md             # Bot long-term memory (shared across all sessions)
│       ├── cron.yaml             # Cron job config (optional)
│       ├── cron_sessions/        # Cron job working directories
│       ├── heartbeat_sessions/   # Heartbeat working directory
│       │   ├── CLAUDE.md
│       │   ├── HEARTBEAT.md      # Checklist (user-editable)
│       │   └── workspace/
│       └── sessions/
│           └── chat_<id>/
│               ├── CLAUDE.md
│               ├── conversation.md
│               ├── .claude_session_id  # Claude Code session ID (for --resume)
│               └── workspace/
├── skills/
│   └── <skill-name>/
│       ├── SKILL.md          # Skill instructions (required)
│       ├── skill.yaml        # Skill config (tool-based skills: type, status, required_commands, install_hints)
│       └── mcp.json          # MCP server config (MCP skills only)
└── logs/
```

## Documentation

- [Architecture](docs/ARCHITECTURE.md)
- [Technical Notes](docs/TECHNICAL-NOTES.md)
- [iMessage Skill Guide](docs/skills/IMESSAGE.md)
- [Apple Reminders Skill Guide](docs/skills/REMINDERS.md)

## Testing

```bash
uv run pytest
# or
pytest
```

## License

MIT
