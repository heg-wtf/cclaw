# Twitter Skill Guide

A guide to installing and using the built-in Twitter/X skill for cclaw.

## Overview

The Twitter skill is an MCP-based skill that lets you post tweets and search tweets through your Telegram bot.
It uses the [@enescinar/twitter-mcp](https://www.npmjs.com/package/@enescinar/twitter-mcp) MCP server.

### Key Features

- Post tweets to your timeline
- Search tweets with Twitter query syntax

## Prerequisites

### 1. Install Node.js

The MCP server runs via `npx`, which requires Node.js.

```bash
# macOS
brew install node

# Verify
npx --version
```

### 2. Twitter/X Developer Portal Setup

1. Go to [X Developer Portal](https://developer.x.com/en/portal/dashboard)
2. Sign up for a developer account (Free tier is sufficient: 500 posts/month)
3. Create a new project and app
4. Set app permissions to **"Read and Write"**
5. Generate the following credentials:
   - **API Key** (Consumer Key)
   - **API Key Secret** (Consumer Secret)
   - **Access Token**
   - **Access Token Secret**

Save all 4 credentials securely. You'll need them during skill setup.

## Installation & Setup

### 1. Install the Built-in Skill

```bash
cclaw skills install twitter
```

### 2. Setup (Activate)

```bash
cclaw skills setup twitter
```

During setup, you'll be prompted to enter:
- `TWITTER_API_KEY` - Your API Key
- `TWITTER_API_SECRET_KEY` - Your API Key Secret
- `TWITTER_ACCESS_TOKEN` - Your Access Token
- `TWITTER_ACCESS_TOKEN_SECRET` - Your Access Token Secret

### 3. Attach the Skill to a Bot

Via Telegram:
```
/skills attach twitter
```

### 4. Verify

```bash
cclaw skills
```

## Usage

After attaching the skill, send natural language requests via Telegram.

### Post a Tweet

```
Tweet "Hello from cclaw!"
Post to twitter: Today's weather is great
```

The bot will always show the full tweet text and ask for confirmation before posting.

### Search Tweets

```
Search tweets about "Claude AI"
Find recent tweets from @anthroploic
Search for #MachineLearning tweets
```

## How It Works

### MCP Server

The skill uses `@enescinar/twitter-mcp` as an MCP server. Claude Code communicates with it via the Model Context Protocol.

```yaml
allowed_tools:
  - "mcp__twitter__post_tweet"
  - "mcp__twitter__search_tweets"
```

### Environment Variable Mapping

The MCP package expects generic env var names (`API_KEY`, etc.), but cclaw uses `TWITTER_`-prefixed names to avoid namespace collision. The `mcp.json` uses a `/bin/sh -c` wrapper to map them:

```
TWITTER_API_KEY      -> API_KEY
TWITTER_API_SECRET_KEY -> API_SECRET_KEY
TWITTER_ACCESS_TOKEN   -> ACCESS_TOKEN
TWITTER_ACCESS_TOKEN_SECRET -> ACCESS_TOKEN_SECRET
```

### Safety Rules

SKILL.md includes guardrails:

- Always confirm with user before posting a tweet
- Enforce 280-character limit
- Never post sensitive or private information
- Never post repetitive or spam-like content

## Rate Limits

| Tier | Monthly Post Cap | Cost |
|------|-----------------|------|
| Free | 500 posts/month | $0 |
| Basic | 3,000 posts/month | $200/month |
| Pro | 300,000 posts/month | $5,000/month |

The Free tier is sufficient for personal use (~16 tweets per day).

## Troubleshooting

### npx command not found

```bash
which npx
# Should output a path like /opt/homebrew/bin/npx
```

**Solution**: Install Node.js via `brew install node`.

### Authentication error (401 Unauthorized)

**Solution**: Verify your credentials are correct in the X Developer Portal. Ensure the app has "Read and Write" permissions. Regenerate Access Token and Secret if needed, then re-run `cclaw skills setup twitter`.

### Rate limit exceeded (429 Too Many Requests)

**Solution**: Wait for the rate limit window to reset. Free tier allows 500 posts per month. Check your current usage in the X Developer Portal.

### Tweet too long

**Solution**: The bot will warn you if the tweet exceeds 280 characters. Shorten the text or ask the bot to trim it.

### MCP server connection error

**Solution**: Ensure Node.js is installed and `npx` works. Try running manually:
```bash
npx -y @enescinar/twitter-mcp
```
If the package downloads but fails, check that the 4 environment variables are set correctly.
