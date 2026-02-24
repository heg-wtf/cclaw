# Supabase Skill Guide

A guide to installing and using the built-in Supabase MCP skill for cclaw.

## Overview

The Supabase skill is an MCP-based skill that gives your Telegram bot access to Supabase Database (PostgreSQL), Storage, and Edge Functions via the Supabase MCP server.

### Key Features

- Query and modify database tables (SELECT, INSERT, UPDATE, CREATE TABLE, ALTER TABLE)
- List tables, extensions, and migrations
- Deploy and inspect Edge Functions
- Manage database branches (create, merge, rebase)
- Generate TypeScript types from schema
- View logs and advisor recommendations

### Safety Guardrails

This skill enforces a strict **no-deletion policy** through two layers of defense:

1. **Hard block**: Destructive MCP tools (`delete_branch`, `reset_branch`, `pause_project`) are excluded from `allowed_tools`, making them impossible to execute in `-p` mode
2. **Soft block**: SKILL.md instructions forbid SQL deletion statements (`DELETE FROM`, `DROP TABLE`, `TRUNCATE`, etc.) and recommend soft delete alternatives

## Prerequisites

### Install Node.js

The Supabase MCP server runs via `npx`, which requires Node.js:

```bash
# macOS
brew install node

# Verify
npx --version
```

### Get Supabase Access Token

1. Go to [Supabase Dashboard](https://supabase.com/dashboard)
2. Navigate to **Account** > **Access Tokens**
3. Create a new token and copy it

## Installation & Setup

### 1. Install the Built-in Skill

```bash
cclaw skills install supabase
```

This creates `SKILL.md`, `skill.yaml`, and `mcp.json` in `~/.cclaw/skills/supabase/`.

### 2. Setup (Activate)

```bash
cclaw skills setup supabase
```

This checks if `npx` is available, then prompts for `SUPABASE_ACCESS_TOKEN`. Enter your access token when prompted.

### 3. Attach the Skill to a Bot

Via Telegram:
```
/skills attach supabase
```

### 4. Verify

```bash
cclaw skills
```

Expected output:
```
supabase (mcp) <- my-bot
```

## Usage

After attaching the skill to a bot, interact with your Supabase project through natural language.

### Query Data

```
Show all users from the users table
Find orders placed in the last 7 days
Count active subscriptions by plan type
```

### Insert Data

```
Add a new record to the places table: name "Seoul Tower", category "landmark"
Insert a test user with email test@example.com
```

### Update Data

```
Update the status of order #123 to "shipped"
Set all expired subscriptions to inactive
```

### Schema Operations

```
Show me the schema of the mustgo_places table
Create a new table called reviews with columns: id, user_id, place_id, rating, content
Add a description column to the places table
```

### Edge Functions

```
List all deployed edge functions
Show the source code of the notify function
Deploy the updated edge function from workspace
```

### Branches

```
List all database branches
Create a new branch called feature-reviews
Merge the feature-reviews branch
```

### What Happens When You Ask to Delete

```
User: Delete all inactive users
Bot: Deletion is not allowed by this skill's safety policy. Instead, I recommend
     using a soft delete approach by adding a `deleted_at` timestamp column...
```

## How It Works

### MCP Server Configuration

The `mcp.json` configures the Supabase MCP server:

```json
{
  "mcpServers": {
    "supabase": {
      "command": "npx",
      "args": ["-y", "@supabase/mcp-server-supabase@latest"]
    }
  }
}
```

During `run_claude()`, this is merged into `.mcp.json` in the session directory. The `SUPABASE_ACCESS_TOKEN` environment variable is injected via `collect_skill_environment_variables()`.

### Dual-Layer Permission Defense

#### Layer 1: allowed_tools (Hard Block)

The `skill.yaml` explicitly lists only safe MCP tools. Destructive tools are excluded:

```yaml
# BLOCKED (not in allowed_tools = no auto-approval in -p mode):
# - mcp__supabase__delete_branch
# - mcp__supabase__reset_branch
# - mcp__supabase__pause_project
# - mcp__supabase__restore_project
```

In Claude Code's `-p` (non-interactive) mode, tools not in `allowed_tools` cannot be auto-approved, effectively making them unusable.

#### Layer 2: SKILL.md Instructions (Soft Block)

For tools that are allowed but can be used destructively (notably `execute_sql`), SKILL.md contains strict instructions:

- Forbidden SQL: `DELETE FROM`, `DROP TABLE`, `DROP SCHEMA`, `TRUNCATE`, `ALTER TABLE ... DROP COLUMN`
- Safe alternatives enforced: soft delete (`is_deleted`, `deleted_at`), archiving, deactivation
- Schema changes must use transactions (`BEGIN`/`COMMIT`)
- RLS policy changes require user confirmation

### Environment Variable Flow

```
skill.yaml (environment_variables: SUPABASE_ACCESS_TOKEN)
  -> cclaw skills setup (user enters token)
  -> skill.yaml (environment_variable_values: {SUPABASE_ACCESS_TOKEN: "sb-xxx..."})
  -> collect_skill_environment_variables()
  -> subprocess env injection
  -> MCP server inherits SUPABASE_ACCESS_TOKEN
```

## Troubleshooting

### npx command not found

```
cclaw skills setup supabase
# Error: required command 'npx' not found
```

**Solution**: Install Node.js:

```bash
brew install node
which npx
# Should output: /opt/homebrew/bin/npx
```

### Bot responds with "Supabase MCP 접근 권한이 필요해요"

**Cause**: Claude Code needs permission to use Supabase MCP tools, but they're not in `allowed_tools` or `.claude/settings.json`.

**Solution**: Verify the skill is properly attached:

```bash
cclaw skills          # Check supabase is active and attached
cclaw skills setup supabase  # Re-run setup if needed
```

If the issue persists, restart the bot (`cclaw stop && cclaw start`).

### MCP server fails to start

**Cause**: `npx` cannot download or run the Supabase MCP server package.

**Solution**: Test manually:

```bash
SUPABASE_ACCESS_TOKEN=your_token npx -y @supabase/mcp-server-supabase@latest
```

Check for network issues or package name changes.

### Access token expired or invalid

**Cause**: The stored `SUPABASE_ACCESS_TOKEN` is no longer valid.

**Solution**: Re-run setup to enter a new token:

```bash
cclaw skills setup supabase
```
