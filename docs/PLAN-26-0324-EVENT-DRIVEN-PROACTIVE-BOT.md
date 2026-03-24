# Event-driven Proactive Bot

**Date**: 2026-03-24
**Branch**: `feature/event-driven-proactive-bot`
**Status**: Draft

## Summary

Extend cclaw so bots can proactively reach out to users based on **external events** (webhooks) and **contextual follow-ups** (enhanced heartbeat), not just fixed-interval polling. Combines idea #4 (Proactive Notification) and #5 (Webhook Receiver) into a unified feature.

## Motivation

Current heartbeat runs on a fixed 30-minute interval with a static HEARTBEAT.md checklist. It can only detect changes by polling the workspace. There is no way for external systems (GitHub, Sentry, CI/CD, custom services) to push events to a bot, and the bot cannot follow up on previous conversations contextually.

**Goal**: Make cclaw bots event-aware and contextually intelligent, so they act as true proactive assistants rather than passive responders.

## Architecture Overview

```
External Systems                    cclaw
┌──────────┐                  ┌─────────────────┐
│ GitHub   │──webhook POST──▶│                 │
│ Sentry   │──webhook POST──▶│  Webhook Server │──▶ event_handler()
│ Custom   │──webhook POST──▶│  (aiohttp)      │     │
└──────────┘                  └─────────────────┘     │
                                                       ▼
                              ┌─────────────────┐  execute_event()
                              │ Heartbeat       │──▶  │
                              │ (enhanced)      │     │
                              └─────────────────┘     ▼
                                                  run_claude_with_sdk()
                                                       │
                                                       ▼
                                                  send_message_callback()
                                                       │
                                                       ▼
                                                  Telegram User
```

## Design Decisions

### D1: Webhook Server Runtime

**Decision**: Use `aiohttp` as the webhook HTTP server, running inside the existing asyncio event loop.

**Why**: cclaw already runs in an asyncio loop (Telegram polling + cron + heartbeat schedulers). aiohttp integrates natively. No need for a separate process or thread. FastAPI/uvicorn would add unnecessary dependencies and complexity.

**Trade-off**: aiohttp is lower-level than FastAPI, but we only need a few routes. The simplicity outweighs the ergonomic cost.

### D2: Webhook Configuration Model

**Decision**: Per-bot `webhooks.yaml` in `bot_directory()`, similar to `cron.yaml`.

**Why**: Follows established pattern. Each bot can receive different webhooks. Config is hot-reloadable (read on each event, like cron).

**Format**:
```yaml
webhooks:
  - name: github-pr-merged
    source: github
    event_types: [pull_request]
    filters:
      action: [closed]
      merged: true
    message_template: |
      GitHub PR merged: {{title}} by {{user}}
      Repository: {{repository}}
      Review and summarize the changes. If relevant to current work, notify the user.
    priority: normal
    skills: []

  - name: sentry-error
    source: sentry
    event_types: [issue]
    filters:
      level: [error, fatal]
    message_template: |
      Sentry alert: {{title}}
      Project: {{project}}
      Analyze this error and suggest a fix.
    priority: high
    skills: []

  - name: custom-deploy
    source: generic
    secret: "webhook-secret-here"
    message_template: |
      Deployment event received: {{payload}}
      Check the status and report.
    priority: normal
    skills: []
```

### D3: Webhook Authentication

**Decision**: Per-webhook `secret` field. Verify via HMAC-SHA256 signature (GitHub-style `X-Hub-Signature-256` header) or Bearer token, depending on `source` type.

**Why**: Different platforms use different auth methods. Source-specific verification prevents unauthorized triggers. Generic webhooks use a shared secret.

### D4: Priority System

**Decision**: Three priority levels — `low`, `normal`, `high`.

**Behavior**:
| Priority | Active Hours | Batching | Delivery |
|----------|-------------|----------|----------|
| `low` | Respected | Batched with next heartbeat | Appended to heartbeat message |
| `normal` | Respected | No batching | Immediate send within active hours, queued otherwise |
| `high` | Ignored | No batching | Immediate send regardless of time |

**Why**: Prevents notification spam while ensuring urgent events reach the user. Low priority events ride on the existing heartbeat cycle, adding zero extra messages.

### D5: Enhanced Heartbeat — Conversation Context

**Decision**: Inject last conversation summary into heartbeat prompt.

**Implementation**: Read the most recent `conversation-YYMMDD.md` from the user's session directory, extract the last 5 exchanges, and prepend to the heartbeat prompt as context.

**Why**: Enables contextual follow-ups like "You mentioned deploying the auth service yesterday — the CI pipeline shows it completed successfully." Without conversation context, heartbeat can only check workspace files.

### D6: Event Execution Model

**Decision**: Reuse the cron/heartbeat execution pattern — dedicated session directory, Claude with context, send result.

**Session key**: `webhook:{bot_name}:{webhook_name}` for SDK pool isolation.
**Working directory**: `~/.cclaw/bots/{name}/webhook_sessions/{webhook_name}/`

**Why**: Proven pattern. Session continuity means the bot remembers previous events of the same type.

### D7: Webhook Server Lifecycle

**Decision**: Webhook server starts/stops as part of `cclaw start`/`cclaw stop`, managed by bot_manager.

**Port**: Configurable in `config.yaml` under `webhook_port` (default: `3848`). Single server shared across all bots. Routes differentiated by bot name in URL path.

**URL pattern**: `POST /webhook/{bot_name}/{webhook_name}`

**Why**: One HTTP server is simpler than per-bot servers. Port 3848 is adjacent to ClawHouse (3847).

## Implementation Plan

### Phase 1: Webhook Infrastructure (Core)

#### Step 1.1: Webhook Configuration CRUD

Create `src/cclaw/webhook.py` with:

```python
# Config CRUD
def load_webhook_config(bot_name: str) -> list[dict]
def save_webhook_config(bot_name: str, webhooks: list[dict]) -> None
def add_webhook(bot_name: str, webhook: dict) -> bool
def remove_webhook(bot_name: str, webhook_name: str) -> bool
def list_webhooks(bot_name: str) -> list[dict]

# Session management
def webhook_session_directory(bot_name: str, webhook_name: str) -> Path

# Validation
def validate_webhook_config(webhook: dict) -> list[str]  # Returns error list
```

**Files**: `src/cclaw/webhook.py` (new)

#### Step 1.2: Webhook Server

Add HTTP server using aiohttp:

```python
# In webhook.py or new webhook_server.py
async def create_webhook_server(
    bot_configs: dict[str, dict],
    send_callbacks: dict[str, Callable],
    stop_event: asyncio.Event,
    port: int = 3848,
) -> aiohttp.web.AppRunner

async def handle_webhook_request(request: aiohttp.web.Request) -> aiohttp.web.Response
    # 1. Extract bot_name, webhook_name from URL
    # 2. Load webhook config
    # 3. Verify signature/secret
    # 4. Parse payload, apply filters
    # 5. Execute event (or queue for batching)
    # 6. Return 200 OK

async def verify_webhook_signature(
    source: str, secret: str, headers: dict, body: bytes
) -> bool
```

**Files**: `src/cclaw/webhook_server.py` (new)
**Dependency**: `aiohttp` (add to `pyproject.toml`)

#### Step 1.3: Event Execution

```python
async def execute_webhook_event(
    bot_name: str,
    bot_config: dict,
    webhook_config: dict,
    payload: dict,
    send_message_callback: Callable,
) -> None
    # 1. Prepare webhook session directory
    # 2. Render message_template with payload variables
    # 3. Prepend memories (global + bot)
    # 4. Run Claude with rendered message
    # 5. Send response to allowed_users
    # Pattern identical to execute_heartbeat / execute_cron_job
```

**Files**: `src/cclaw/webhook.py`

#### Step 1.4: CLI Commands

Add to `cli.py`:

```
cclaw webhook list <bot>              # List configured webhooks
cclaw webhook add <bot>               # Interactive webhook setup
cclaw webhook remove <bot> <name>     # Remove a webhook
cclaw webhook test <bot> <name>       # Send test payload
cclaw webhook url <bot> <name>        # Show the webhook URL
```

**Files**: `src/cclaw/cli.py`

#### Step 1.5: Bot Manager Integration

In `bot_manager.py`:
- Start webhook server in `_run_bots()` after polling starts
- Pass `send_callbacks` dict (bot_name → `application.bot.send_message`)
- Stop server in the `finally` block (graceful shutdown)
- Add webhook server status to `cclaw status` output

**Files**: `src/cclaw/bot_manager.py`

### Phase 2: Priority and Batching

#### Step 2.1: Priority Queue

Create an in-memory event queue for batching low-priority events:

```python
# In webhook.py
class EventQueue:
    def __init__(self):
        self._queue: dict[str, list[dict]] = {}  # bot_name -> events

    async def enqueue(self, bot_name: str, event: dict) -> None
    async def drain(self, bot_name: str) -> list[dict]
    def has_pending(self, bot_name: str) -> bool
```

**Files**: `src/cclaw/webhook.py`

#### Step 2.2: Heartbeat Integration

Modify `execute_heartbeat()` to:
1. Check `EventQueue` for pending low-priority events
2. Append event summaries to the heartbeat prompt
3. Clear the queue after successful delivery

**Files**: `src/cclaw/heartbeat.py`

#### Step 2.3: Active Hours Gating

For `normal` priority events received outside active hours:
- Store in a persistent queue file (`~/.cclaw/bots/{name}/pending_events.yaml`)
- Deliver when active hours resume (checked by heartbeat scheduler)

**Files**: `src/cclaw/webhook.py`, `src/cclaw/heartbeat.py`

### Phase 3: Enhanced Heartbeat

#### Step 3.1: Conversation Context Injection

Add to `heartbeat.py`:

```python
def load_recent_conversation_context(bot_name: str, max_exchanges: int = 5) -> str
    # 1. Find the most recent session directory (by last modified)
    # 2. Read the latest conversation-YYMMDD.md
    # 3. Extract last N exchanges
    # 4. Return formatted summary
```

Modify `execute_heartbeat()` to prepend conversation context to the prompt.

**Files**: `src/cclaw/heartbeat.py`, `src/cclaw/session.py`

#### Step 3.2: Smart Follow-up Detection

Enhance HEARTBEAT.md template with follow-up instructions:

```markdown
## Follow-up Rules

- Review the recent conversation context below
- If the user mentioned a pending task, check if it can be resolved now
- If a deployment or CI was discussed, check current status
- Only notify if you have actionable information, not just "checking in"
```

**Files**: `src/cclaw/heartbeat.py` (default template)

#### Step 3.3: Heartbeat Priority Override

Allow HEARTBEAT.md to output priority markers:

- `HEARTBEAT_OK` — no notification (existing)
- `HEARTBEAT_HIGH` — send immediately regardless of batching
- Default (no marker) — send as normal priority

**Files**: `src/cclaw/heartbeat.py`

### Phase 4: Source-specific Parsers

#### Step 4.1: GitHub Webhook Parser

```python
def parse_github_payload(event_type: str, payload: dict) -> dict
    # Normalize GitHub webhook payload into template variables:
    # title, user, repository, action, url, branch, etc.
```

Supports: `push`, `pull_request`, `issues`, `release`, `workflow_run`

#### Step 4.2: Sentry Webhook Parser

```python
def parse_sentry_payload(payload: dict) -> dict
    # Normalize: title, project, level, url, stacktrace_summary
```

#### Step 4.3: Generic Webhook Parser

```python
def parse_generic_payload(payload: dict) -> dict
    # Pass-through with JSON summary: payload (truncated to 2000 chars)
```

**Files**: `src/cclaw/webhook_parsers.py` (new)

### Phase 5: Dashboard Integration

#### Step 5.1: Webhook Management UI

- List webhooks per bot in bot detail page
- Add/edit/delete webhook configurations
- Show webhook URL with copy button
- Test webhook button (sends mock payload)

#### Step 5.2: Event History

- Log each webhook event to `~/.cclaw/bots/{name}/webhook_sessions/{name}/events.jsonl`
- Display in dashboard: timestamp, source, payload summary, response preview, delivery status

**Files**: `clawhouse/src/app/bots/[name]/webhooks/page.tsx` (new), `clawhouse/lib/cclaw.ts`

### Phase 6: Telegram Commands

#### Step 6.1: `/webhooks` Command

Show active webhook configurations and recent event counts:

```
Webhooks for bot:

github-pr-merged (github)
  URL: http://host:3848/webhook/mybot/github-pr-merged
  Events today: 3

sentry-error (sentry)
  URL: http://host:3848/webhook/mybot/sentry-error
  Events today: 0
```

#### Step 6.2: `/mute` and `/unmute` Commands

Temporarily suppress proactive notifications:

- `/mute 2h` — mute all proactive messages for 2 hours
- `/mute` — mute until `/unmute`
- `/unmute` — resume notifications

**Files**: `src/cclaw/handlers.py`

## File Change Summary

| File | Action | Description |
|------|--------|-------------|
| `src/cclaw/webhook.py` | New | Webhook config CRUD, event execution, priority queue |
| `src/cclaw/webhook_server.py` | New | aiohttp HTTP server, request handling, signature verification |
| `src/cclaw/webhook_parsers.py` | New | GitHub, Sentry, generic payload parsers |
| `src/cclaw/heartbeat.py` | Modify | Conversation context injection, event queue drain, priority markers |
| `src/cclaw/session.py` | Modify | Add `load_recent_conversation_context()` |
| `src/cclaw/bot_manager.py` | Modify | Start/stop webhook server, pass send callbacks |
| `src/cclaw/handlers.py` | Modify | Add `/webhooks`, `/mute`, `/unmute` handlers |
| `src/cclaw/cli.py` | Modify | Add `webhook` subcommand group |
| `src/cclaw/config.py` | Modify | Add `webhook_port` config field |
| `pyproject.toml` | Modify | Add `aiohttp` dependency |
| `clawhouse/` | New pages | Webhook management UI, event history |

## Runtime Data Structure Changes

```
~/.cclaw/
├── config.yaml                        # + webhook_port: 3848
├── bots/<name>/
│   ├── webhooks.yaml                  # NEW: webhook configurations
│   ├── pending_events.yaml            # NEW: queued events (normal priority, outside active hours)
│   ├── webhook_sessions/<webhook>/    # NEW: per-webhook session
│   │   ├── CLAUDE.md
│   │   ├── workspace/
│   │   └── events.jsonl               # Event history log
│   └── heartbeat_sessions/
│       └── HEARTBEAT.md               # Updated template with follow-up rules
```

## Test Plan

### Unit Tests (Phase 1-4)

| Test | Module | Description |
|------|--------|-------------|
| `test_webhook_config_crud` | webhook.py | Add, remove, list, validate webhook configs |
| `test_webhook_session_directory` | webhook.py | Directory creation, CLAUDE.md copy |
| `test_validate_webhook_config` | webhook.py | Missing fields, invalid source, bad cron |
| `test_verify_github_signature` | webhook_server.py | HMAC-SHA256 verification (valid/invalid/missing) |
| `test_verify_bearer_token` | webhook_server.py | Bearer token auth for generic webhooks |
| `test_handle_webhook_request_valid` | webhook_server.py | Full request → execution flow (mocked Claude) |
| `test_handle_webhook_request_invalid_signature` | webhook_server.py | Returns 401 on bad signature |
| `test_handle_webhook_request_unknown_bot` | webhook_server.py | Returns 404 for non-existent bot |
| `test_handle_webhook_request_filter_mismatch` | webhook_server.py | Returns 200 but skips execution when filters don't match |
| `test_execute_webhook_event` | webhook.py | Claude called with rendered template, message sent |
| `test_event_queue_enqueue_drain` | webhook.py | Enqueue, drain, has_pending correctness |
| `test_priority_high_ignores_active_hours` | webhook.py | High priority bypasses active hours check |
| `test_priority_low_batched_with_heartbeat` | heartbeat.py | Low priority events appended to heartbeat prompt |
| `test_pending_events_persist` | webhook.py | Normal priority events saved to YAML when outside active hours |
| `test_parse_github_pr_merged` | webhook_parsers.py | PR merged payload → template variables |
| `test_parse_github_push` | webhook_parsers.py | Push payload → template variables |
| `test_parse_sentry_error` | webhook_parsers.py | Sentry issue payload → template variables |
| `test_parse_generic_payload` | webhook_parsers.py | Arbitrary JSON → truncated payload string |
| `test_recent_conversation_context` | session.py | Extract last N exchanges from conversation log |
| `test_heartbeat_with_conversation_context` | heartbeat.py | Conversation context prepended to heartbeat prompt |
| `test_heartbeat_priority_markers` | heartbeat.py | HEARTBEAT_HIGH triggers immediate send |
| `test_mute_unmute` | handlers.py | /mute suppresses, /unmute resumes notifications |
| `test_cli_webhook_list` | cli.py | CLI output matches webhook config |
| `test_cli_webhook_add_remove` | cli.py | Add/remove updates webhooks.yaml |

### Integration Tests

| Test | Description |
|------|-------------|
| `test_webhook_server_startup_shutdown` | Server starts on configured port, shuts down cleanly |
| `test_webhook_end_to_end` | HTTP POST → Claude execution → Telegram message (all mocked) |
| `test_heartbeat_drains_event_queue` | Heartbeat cycle includes queued low-priority events |
| `test_bot_manager_with_webhooks` | Full bot startup includes webhook server |
| `test_pending_events_delivered_on_active_hours` | Events queued at night delivered in morning |

### Manual Verification

1. Configure a GitHub webhook pointing to `http://<host>:3848/webhook/<bot>/github-pr-merged`
2. Merge a PR → verify bot sends notification via Telegram
3. Configure a Sentry webhook → trigger an error → verify alert
4. Set a low-priority webhook → verify it arrives with next heartbeat
5. Test `/mute 1h` → verify no notifications → `/unmute` → verify resumption
6. Test high-priority event outside active hours → verify immediate delivery
7. Verify `cclaw status` shows webhook server info
8. Verify `cclaw webhook test <bot> <name>` sends test event

### Security Checklist

- [ ] Webhook secrets never logged or exposed in error messages
- [ ] HMAC signature verification uses constant-time comparison (`hmac.compare_digest`)
- [ ] Payload size limited (reject bodies > 1MB)
- [ ] Rate limiting per source IP (prevent DoS)
- [ ] Bot name and webhook name validated against path traversal (`..` in URL)
- [ ] Generic webhook secret is required (no unauthenticated endpoints)
- [ ] Webhook URLs not exposed in Telegram messages

## Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| `aiohttp` | `>=3.9` | Webhook HTTP server |

No other new dependencies required. All other functionality uses existing packages (PyYAML, croniter, python-telegram-bot).

## Migration

No breaking changes. Existing bots continue to work without webhook configuration. The webhook server only starts if at least one bot has `webhooks.yaml` with entries, or can be configured to always start via `config.yaml`.

## Future Extensions

- **Outbound webhooks**: Bot sends HTTP requests on conversation events (e.g., notify Slack when a task is completed)
- **Webhook templates marketplace**: Pre-built webhook configs for common services
- **Conditional webhooks**: Filter by payload content using JSONPath expressions
- **Webhook chaining**: Output of one webhook triggers another bot's action
