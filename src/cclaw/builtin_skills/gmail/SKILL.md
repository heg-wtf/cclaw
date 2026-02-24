# Gmail

Gmail integration via `gog` (gogcli). Search, read, send emails, manage labels and drafts.

## Prerequisites

- `gog` CLI installed (`brew install steipete/tap/gogcli`)
- Google account authorized: `gog auth add you@gmail.com`
- `GOG_ACCOUNT` environment variable set during skill setup

## Safety Rules

- **Always confirm with the user before sending an email.** Show recipient, subject, and body before sending.
- **Never delete emails.** Use archive or label management instead.
- **Never modify filters or delegation settings** without explicit user approval.
- When forwarding or replying, confirm the recipient to avoid accidental leaks.

## Available Commands

### Search Emails

```bash
gog gmail search 'query' [--limit N] [--json]
```

- Uses Gmail search syntax (same as Gmail web search bar)
- Common queries:
  - `newer_than:1d` — Last 24 hours
  - `newer_than:7d` — Last 7 days
  - `from:someone@example.com` — From specific sender
  - `subject:meeting` — Subject contains "meeting"
  - `is:unread` — Unread messages
  - `has:attachment` — Has attachments
  - `label:important` — Labeled important
- `--limit N`: Number of results (default: 10)
- `--json`: JSON output for structured parsing

### Read a Message

```bash
gog gmail message get <messageId> [--json]
```

- Shows full message content (headers, body, attachments)
- Get `messageId` from search results

### Read a Thread

```bash
gog gmail thread get <threadId> [--json]
```

- Shows all messages in a conversation thread
- Get `threadId` from search results

### Send Email

```bash
gog gmail send --to 'recipient@example.com' --subject 'Subject' --body 'Body text'
```

- `--to`: Recipient email (required)
- `--subject`: Email subject (required)
- `--body`: Email body text
- `--cc`: CC recipients
- `--bcc`: BCC recipients
- `--attach`: File attachment path

### Reply to Email

```bash
gog gmail send --to 'recipient@example.com' --subject 'Re: Original Subject' --body 'Reply text' --thread <threadId> --in-reply-to <messageId>
```

- `--thread`: Thread ID to reply in
- `--in-reply-to`: Message ID being replied to

### List Labels

```bash
gog gmail labels list [--json]
```

### Manage Labels

```bash
gog gmail message label <messageId> --add 'LabelName'
gog gmail message label <messageId> --remove 'LabelName'
```

### Archive Email

```bash
gog gmail message label <messageId> --remove 'INBOX'
```

### List Drafts

```bash
gog gmail drafts list [--limit N] [--json]
```

### Create Draft

```bash
gog gmail drafts create --to 'recipient@example.com' --subject 'Subject' --body 'Body'
```

## Usage Guidelines

- Use `--json` for structured output when parsing is needed.
- Search with specific queries to narrow down results efficiently.
- For email summaries, search first then read individual messages/threads.
- When user asks about "recent emails", use `newer_than:1d` or `newer_than:7d`.
- When user asks to "check email from someone", use `from:email@example.com`.
- Always present email content in a readable format (sender, subject, date, body summary).
- For long email threads, summarize key points rather than showing everything.
