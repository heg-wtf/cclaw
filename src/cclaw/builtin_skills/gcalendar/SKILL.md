# Google Calendar

Google Calendar integration via `gog` (gogcli). View, create, update events and check availability.

## Prerequisites

- `gog` CLI installed (`brew install steipete/tap/gogcli`)
- Google account authorized: `gog auth add you@gmail.com`
- `GOG_ACCOUNT` environment variable set during skill setup

## Safety Rules

- **Always confirm with the user before creating or modifying events.** Show date, time, title, and attendees before proceeding.
- **Never delete events.** Suggest cancellation or declining instead.
- **Never accept/decline invitations** without explicit user approval.
- When creating events with attendees, confirm the attendee list to avoid accidental invitations.

## Available Commands

### List Today's Events

```bash
gog calendar events --today [--json]
```

### List Events for a Date Range

```bash
gog calendar events --from 'YYYY-MM-DD' --to 'YYYY-MM-DD' [--json]
```

- `--from`: Start date (inclusive)
- `--to`: End date (inclusive)
- `--json`: JSON output for structured parsing

### List Upcoming Events

```bash
gog calendar events --upcoming [--limit N] [--json]
```

- Shows future events from now
- `--limit N`: Number of events to show

### Get Event Details

```bash
gog calendar event get <eventId> [--json]
```

### Create Event

```bash
gog calendar event create --title 'Meeting' --start '2026-02-25T14:00:00' --end '2026-02-25T15:00:00' [--description 'Details'] [--location 'Room A'] [--attendee 'person@example.com']
```

- `--title`: Event title (required)
- `--start`: Start datetime in ISO format (required)
- `--end`: End datetime in ISO format (required)
- `--description`: Event description
- `--location`: Location
- `--attendee`: Attendee email (can be repeated for multiple attendees)
- `--all-day`: Create an all-day event (use date format `YYYY-MM-DD`)

### Update Event

```bash
gog calendar event update <eventId> [--title 'New Title'] [--start 'datetime'] [--end 'datetime'] [--description 'New desc'] [--location 'New location']
```

### RSVP to Event

```bash
gog calendar event rsvp <eventId> --status accepted
gog calendar event rsvp <eventId> --status declined
gog calendar event rsvp <eventId> --status tentative
```

### Check Free/Busy

```bash
gog calendar freebusy --from 'YYYY-MM-DDTHH:MM:SS' --to 'YYYY-MM-DDTHH:MM:SS' [--attendee 'person@example.com'] [--json]
```

- Check availability for yourself or others
- `--attendee`: Check another person's availability (can be repeated)

### Detect Conflicts

```bash
gog calendar events --from 'YYYY-MM-DD' --to 'YYYY-MM-DD' --detect-conflicts [--json]
```

### List Calendars

```bash
gog calendar list [--json]
```

## Usage Guidelines

- Use `--json` for structured output when parsing is needed.
- When user asks "what's on my schedule today", use `--today`.
- When user asks about a specific date, use `--from` and `--to` with the same date.
- When user asks "am I free at 3pm?", use `freebusy` to check availability.
- Always present events in a readable format (title, time, location, attendees).
- Use ISO 8601 datetime format for `--start` and `--end` (e.g., `2026-02-25T14:00:00`).
- For recurring events, show the next occurrence and mention the recurrence pattern.
- When suggesting meeting times, check free/busy first to avoid conflicts.
