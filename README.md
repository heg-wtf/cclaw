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

## Design Principles

- **Local First**: No server required. Long Polling. No SSL or public IP needed.
- **File Based**: No database. Session = directory. Conversation = markdown.
- **Claude Code Delegation**: No direct LLM API calls. Runs `claude -p` as a subprocess.
- **CLI First**: Everything from onboarding to bot management is done in the terminal.

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
```

## Telegram Commands

| Command | Description |
|---------|-------------|
| `/start` | Bot introduction |
| `/reset` | Clear conversation (keep workspace) |
| `/resetall` | Delete entire session |
| `/files` | List workspace files |
| `/send <filename>` | Send workspace file |
| `/status` | Session status |
| `/model` | Show current model |
| `/model <name>` | Change model (sonnet/opus/haiku) |
| `/streaming` | Show streaming status |
| `/streaming on/off` | Toggle streaming mode |
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
│   ├── builtin_skills/     # Built-in skill templates (imessage, ...)
│   │   ├── __init__.py     # Built-in skill registry
│   │   └── imessage/       # iMessage skill (imsg CLI)
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
- [iMessage Skill Guide](docs/IMESSAGE-SKILL.md)

## Testing

```bash
uv run pytest
# or
pytest
```

## License

MIT
