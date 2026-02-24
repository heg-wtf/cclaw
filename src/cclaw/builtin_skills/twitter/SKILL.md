# Twitter

Twitter/X integration via MCP. Post tweets and search tweets.

## Prerequisites

- Node.js installed (`npx` available)
- Twitter/X Developer Portal account (Free tier is sufficient)
- API credentials: API Key, API Secret Key, Access Token, Access Token Secret
- App permissions set to "Read and Write" in the Developer Portal

## Setup Guide

1. Go to X Developer Portal (https://developer.x.com/en/portal/dashboard)
2. Create a new project and app (Free tier: 500 posts/month)
3. Set app permissions to "Read and Write"
4. Generate API Key, API Secret Key, Access Token, and Access Token Secret
5. Run `cclaw skills setup twitter` to enter the credentials

## Safety Rules

- **Always show the full tweet text to the user and ask for confirmation before posting.** Never post without explicit user approval.
- **280-character limit**: Ensure the tweet text does not exceed 280 characters. If it does, suggest trimming or splitting.
- **Never post sensitive or private information** (passwords, API keys, personal addresses, phone numbers, etc.).
- **Never post repetitive or spam-like content.**
- When user asks to "tweet" or "post", always compose the text first, show it, then post after confirmation.

## Available Operations

### Post Tweet

Post a new tweet to the authenticated user's timeline.

- Always compose the tweet text first and show it to the user
- Confirm with the user before posting
- Character limit: 280 characters
- After posting, report the result (success or failure)

### Search Tweets

Search for tweets matching a query.

- Supports Twitter search syntax
- Common queries:
  - `from:username` - Tweets from a specific user
  - `to:username` - Tweets replying to a user
  - `keyword` - Tweets containing a keyword
  - `#hashtag` - Tweets with a specific hashtag
  - `keyword lang:ko` - Korean tweets with keyword
- Present search results in a readable format (author, text, date)

## Usage Guidelines

- When the user says "tweet this" or "post to twitter", compose the text and confirm before posting.
- For long text, suggest splitting into a thread or trimming to fit the character limit.
- When composing tweets, consider:
  - Appropriate hashtags if relevant
  - Mentions (@username) if needed
  - URL shortening is handled automatically by Twitter
- For search results, summarize key information rather than showing raw data.
- If the post fails, report the error clearly and suggest possible fixes (e.g., check credentials, rate limit exceeded).

## Rate Limits

- Free tier: 500 posts per month (~16 per day)
- Search: Limited on Free tier
- If rate limited, inform the user and suggest waiting
