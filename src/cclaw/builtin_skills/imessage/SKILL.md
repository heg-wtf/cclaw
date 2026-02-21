# iMessage

macOS iMessage/SMS integration skill. Uses the `imsg` CLI tool to read and send messages.
Uses `osascript` to look up phone numbers by name from macOS Contacts.

## Contact Lookup

When a user requests a message by name, look up the phone number from Contacts first.

### Search Contacts by Name

```bash
osascript -e 'tell application "Contacts" to get {name, value of phones} of every person whose name contains "search term"'
```

- Partial matching is supported. Searching "John" will also match "John Smith".
- If multiple results are returned, ask the user to confirm the correct contact.
- Extract the phone number from the result and use it with `imsg send --to`.

### Contact Lookup -> Message Send Flow

1. User: "Send hello to John Smith"
2. Search "John" or "John Smith" via `osascript` -> Confirm phone number
3. Ask user to confirm recipient and content
4. After approval: `imsg send --to +821012345678 --text "hello"`

## Available Commands

### List Conversations

```bash
imsg chats [--limit N] [--json]
```

- Shows recent conversation list
- `--limit N`: Limit number of conversations shown (default: 20)
- `--json`: Output in JSON format

### View Message History

```bash
imsg history --chat-id <id> [--limit N] [--json]
```

- Views message history for a specific conversation
- `--chat-id`: Conversation ID (check via chats command)
- `--limit N`: Limit number of messages shown (default: 50)
- `--json`: Output in JSON format

### Send Message

```bash
imsg send --to <handle> [--text "message"] [--file /path/to/file]
```

- Sends a message or file
- `--to`: Recipient (phone number or email)
- `--text`: Text message
- `--file`: Attachment file path

### Real-Time Monitoring

```bash
imsg watch [--chat-id <id>] [--json]
```

- Monitors new messages in real-time
- `--chat-id`: Monitor specific conversation only (all if omitted)
- `--json`: Output in JSON format

## Usage Guidelines

- **Always confirm with the user before sending a message.** Never send without confirmation.
- When user requests by name, look up contacts via `osascript` first.
- Using `--json` option makes structured data easier to parse.
- Check chat-id from the conversation list before viewing history.
- Phone number format: `+821012345678` (international format recommended)
- Use absolute paths when sending files.
