# Jira Skill Guide

A guide to installing and using the built-in Jira skill for cclaw.

## Overview

The Jira skill is an MCP-based skill that lets you manage Jira issues through your Telegram bot.
It uses the [sooperset/mcp-atlassian](https://github.com/sooperset/mcp-atlassian) MCP server.

### Key Features

- Search issues with JQL (Jira Query Language)
- Get detailed issue information
- Create new issues
- Update existing issues
- Transition issue workflow status

## Prerequisites

### 1. Install uv

The MCP server runs via `uvx` (included with `uv`).

```bash
# macOS
brew install uv

# Verify
uvx --version
```

### 2. Atlassian API Token

1. Go to [Atlassian API Token page](https://id.atlassian.com/manage-profile/security/api-tokens)
2. Click **"Create API token"**
3. Give it a label (e.g., "cclaw bot") and click **"Create"**
4. Copy the token immediately (it won't be shown again)

You'll need:
- **Jira URL**: Your instance URL (e.g., `https://your-company.atlassian.net`)
- **Username**: Your Atlassian account email
- **API Token**: The token you just created

## Installation & Setup

### 1. Install the Built-in Skill

```bash
cclaw skills install jira
```

### 2. Setup (Activate)

```bash
cclaw skills setup jira
```

During setup, you'll be prompted to enter:
- `JIRA_URL` - Your Jira instance URL
- `JIRA_USERNAME` - Your Atlassian account email
- `JIRA_API_TOKEN` - Your API token

### 3. Attach the Skill to a Bot

Via Telegram:
```
/skills attach jira
```

### 4. Verify

```bash
cclaw skills
```

## Usage

After attaching the skill, send natural language requests via Telegram.

### Search Issues

```
Show me my open issues
Find all bugs in project PROJ
What issues are in the current sprint?
Show high priority issues assigned to me
```

### Get Issue Details

```
Show me PROJ-123
What's the status of PROJ-456?
```

### Create Issue

```
Create a bug in PROJ: Login button not working on mobile
Create a task in PROJ: Update API documentation
```

The bot will show the issue details and ask for confirmation before creating.

### Update Issue

```
Change the priority of PROJ-123 to High
Add label "urgent" to PROJ-456
Update description of PROJ-789 to include the new requirements
```

### Transition Issue

```
Move PROJ-123 to In Progress
Mark PROJ-456 as Done
Close PROJ-789
```

The bot will show the current status and target status before transitioning.

## How It Works

### MCP Server

The skill uses `mcp-atlassian` as an MCP server via `uvx`. Claude Code communicates with it via the Model Context Protocol.

```yaml
allowed_tools:
  - "mcp__jira__jira_search"
  - "mcp__jira__jira_get_issue"
  - "mcp__jira__jira_create_issue"
  - "mcp__jira__jira_update_issue"
  - "mcp__jira__jira_transition_issue"
```

### Environment Variables

The environment variables (`JIRA_URL`, `JIRA_USERNAME`, `JIRA_API_TOKEN`) are stored during `cclaw skills setup` and injected into the Claude Code subprocess at runtime. The MCP server inherits them from the process environment.

### Safety Rules

SKILL.md includes guardrails:

- Always confirm before creating issues
- Always confirm before transitioning issues
- Never bulk-modify without approval
- Never delete issues (suggest closing instead)

## JQL Quick Reference

| Query | Description |
|-------|-------------|
| `project = PROJ` | All issues in project |
| `assignee = currentUser()` | My issues |
| `status = "In Progress"` | Issues in progress |
| `priority = High` | High priority issues |
| `created >= -7d` | Created in last 7 days |
| `updated >= -1d` | Updated in last day |
| `text ~ "keyword"` | Full text search |
| `sprint in openSprints()` | Current sprint |
| `type = Bug AND status != Done` | Open bugs |
| `labels = "urgent"` | Issues with label |

## Troubleshooting

### uvx command not found

```bash
which uvx
```

**Solution**: Install uv via `brew install uv` or `curl -LsSf https://astral.sh/uv/install.sh | sh`.

### Authentication error (401 Unauthorized)

**Solution**: Verify your credentials:
1. Check that `JIRA_URL` is correct (e.g., `https://your-company.atlassian.net`, not `https://your-company.atlassian.net/jira`)
2. Verify `JIRA_USERNAME` is your email address
3. Regenerate the API token and re-run `cclaw skills setup jira`

### Permission denied (403 Forbidden)

**Solution**: Your Atlassian account may not have access to the requested project. Check your Jira permissions with your admin.

### MCP server connection error

**Solution**: Ensure `uvx` works and the package can be downloaded:
```bash
uvx mcp-atlassian --help
```

If the package fails to download, check your internet connection and Python version (requires Python >= 3.11).
