# Apple Reminders

macOS Reminders integration skill. Uses the `reminders` CLI tool to view, create, and complete reminders.

## Available Commands

### List All Reminder Lists

```bash
reminders show-lists
```

### View Reminders in a Specific List

```bash
reminders show <list_name>
reminders show <list_name> --include-completed
```

### Create a Reminder

```bash
reminders add <list_name> "<title>"
reminders add <list_name> "<title>" --due-date "2026-02-22"
reminders add <list_name> "<title>" --due-date "tomorrow 9am" --priority high
reminders add <list_name> "<title>" --notes "Note content"
```

### Complete a Reminder

```bash
reminders complete <list_name> <index>
```

### Delete a Reminder

```bash
reminders delete <list_name> <index>
```

### View Today's Reminders

```bash
reminders show-all --due-date today
```

### View Overdue Reminders

```bash
reminders show-all --include-overdue
```

## Usage Guidelines

- There may be multiple reminder lists, so check with show-lists first.
- Before creating a reminder, confirm the title, list, and date with the user.
- Always confirm with the user before completing or deleting a reminder.
- Index numbers can be found in the output of the show command.
