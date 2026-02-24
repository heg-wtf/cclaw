# Security Audit

Last audited: 2026-02-25

## Summary

Total issues found: 33 (Critical: 5, High: 4, Medium: 5, Low/Info: 19)

## Critical

### 1. Path Traversal in /send Command

- **File**: `src/cclaw/handlers.py` (lines 217-226)
- **Status**: Open
- **Description**: The `/send` command constructs file paths using unsanitized user input. Sending `../../../etc/passwd` can access files outside the workspace directory.
- **Fix**: Validate with `file_path.resolve().relative_to(workspace.resolve())` and reject on `ValueError`.

### 2. Path Traversal in File Download

- **File**: `src/cclaw/handlers.py` (lines 675-676)
- **Status**: Open
- **Description**: Files downloaded from Telegram are saved with the original filename from the sender. A filename like `../../exploit.sh` can write files outside the workspace.
- **Fix**: Sanitize filenames — strip path separators and `..`, or use a deterministic naming scheme like `file_{hash}{extension}`.

### 3. Telegram Token Stored in Plaintext

- **File**: `src/cclaw/onboarding.py` (line 185), `src/cclaw/config.py`
- **Status**: Open
- **Description**: Telegram bot tokens are saved directly to `bot.yaml` without encryption. If the home directory is compromised, tokens are immediately accessible.
- **Fix**: Use macOS Keychain via `keyring` library, or encrypt tokens at rest.

### 4. Cron Job Name Not Validated

- **File**: `src/cclaw/cron.py` (line 95), `src/cclaw/cli.py`
- **Status**: Open
- **Description**: Job name from user input is used directly in `cron_sessions/{job_name}/` directory creation. Path traversal sequences like `../` can escape the intended directory.
- **Fix**: Validate job name with `^[a-z0-9][a-z0-9_-]{0,63}$`.

### 5. Environment Variable Injection via Skills

- **File**: `src/cclaw/claude_runner.py` (lines 168, 232-234)
- **Status**: Open
- **Description**: Skill environment variables are merged into `os.environ` without validation. Malicious skill configs could override critical system variables (e.g., `PATH`, `HOME`).
- **Fix**: Whitelist allowed environment variable prefixes per skill. Reject variables that override system-critical names.

## High

### 6. No Rate Limiting on Messages

- **File**: `src/cclaw/handlers.py` (message_handler, file_handler)
- **Status**: Open
- **Description**: Users can send unlimited messages, each spawning a Claude subprocess. This can exhaust CPU, memory, and file handles.
- **Fix**: Implement per-user rate limiting (e.g., sliding window, max 1 message per 10 seconds).

### 7. Bot Name Validation Insufficient

- **File**: `src/cclaw/onboarding.py` (lines 161-170)
- **Status**: Open
- **Description**: Bot name allows names starting with `.` (hidden directories) and has no length limit. Used directly in directory creation.
- **Fix**: Enforce `^[a-z0-9][a-z0-9-]{0,62}$`.

### 8. Absolute Path Exposed in CLAUDE.md

- **File**: `src/cclaw/skill.py` (line 324)
- **Status**: Open
- **Description**: The absolute filesystem path to `MEMORY.md` is embedded in the generated CLAUDE.md system prompt. Reveals system directory structure.
- **Fix**: Use relative path or abstract description.

### 9. Message Content Logged

- **File**: `src/cclaw/claude_runner.py` (line 176)
- **Status**: Open
- **Description**: User messages are logged (truncated to 100 chars). Could contain passwords, tokens, or PII.
- **Fix**: Log only metadata (message length, timestamp) instead of content.

## Medium

### 10. Conversation History Unlimited Growth

- **File**: `src/cclaw/session.py`
- **Status**: Open
- **Description**: `conversation.md` is appended indefinitely with no size limit. A user sending thousands of messages can exhaust disk space.
- **Fix**: Implement max file size (e.g., 10MB) or message count cap with archival.

### 11. No Workspace Size Limit

- **File**: `src/cclaw/session.py` (workspace directory)
- **Status**: Open
- **Description**: Workspace directories have no quota. Large file uploads can fill the disk.
- **Fix**: Check workspace size before download, enforce per-session quota (e.g., 100MB).

### 12. HEARTBEAT_OK Marker Spoofable

- **File**: `src/cclaw/heartbeat.py` (line 228)
- **Status**: Open
- **Description**: Heartbeat response is checked with `HEARTBEAT_OK_MARKER in response`. If the LLM echoes user input containing "HEARTBEAT_OK", notifications are suppressed.
- **Fix**: Use structured response format or stricter pattern matching.

### 13. Error Messages Expose Internal Paths

- **File**: `src/cclaw/handlers.py` (lines 221, 225, 628, 716)
- **Status**: Open
- **Description**: Error responses sent to Telegram users include internal paths and exception details.
- **Fix**: Send generic error messages to users, log full details internally.

### 14. No Timeout on File Download

- **File**: `src/cclaw/handlers.py` (line 676)
- **Status**: Open
- **Description**: `file.download_to_drive()` has no explicit timeout. Slow or large downloads can hang the handler indefinitely.
- **Fix**: Wrap with `asyncio.wait_for(..., timeout=60)`.

## Low / Informational

### 15. Session ID Entropy

- **File**: `src/cclaw/handlers.py` (line 508)
- **Description**: Uses `uuid.uuid4()` for session IDs. `secrets.token_urlsafe(32)` provides higher entropy.

### 16. No CSRF Protection for Destructive Commands

- **File**: `src/cclaw/handlers.py`
- **Description**: `/resetall` deletes session without confirmation. Consider requiring `/resetall confirm`.

### 17. MCP Config Written in Plaintext

- **File**: `src/cclaw/claude_runner.py` (lines 162-164)
- **Description**: `.mcp.json` with potential credentials is stored in plaintext in session directories.

### 18. Launchd Plist Embeds Current PATH

- **File**: `src/cclaw/bot_manager.py` (lines 238, 254)
- **Description**: Full current `PATH` is copied into the launchd plist file.

### 19. No Audit Logging

- **File**: Various handlers
- **Description**: No structured audit log of user actions (who, what, when).

### 20. Exception Details Sent to Users

- **File**: `src/cclaw/handlers.py` (lines 628, 716)
- **Description**: Full `str(error)` is sent in Telegram responses. Could leak internal details.

### 21. Subprocess Timeout Cleanup

- **File**: `src/cclaw/claude_runner.py` (lines 191-193)
- **Description**: Timeout sends SIGKILL directly. Consider SIGTERM first with a grace period.

### 22. No Config Schema Validation

- **File**: Various YAML loaders
- **Description**: YAML files have no schema validation. Corrupted configs can cause crashes.

### 23. Skill Installation Integrity

- **File**: `src/cclaw/skill.py` (lines 439-441)
- **Description**: Builtin skills are copied without checksum verification.

### 24-33. Additional Minor Items

- Chat ID not validated as positive integer (`session.py:17`)
- No HTTPS validation for MCP server URLs (`skill.py`)
- No file size check before Telegram download
- Hardcoded language strings (Korean only)
- `.gitignore` should cover `bot.yaml` and `.mcp.json`
- No workspace file type restrictions
- `collect_session_chat_ids` could return stale sessions
- Race condition between `lock.locked()` check and `async with lock` (`handlers.py:591`)
- Regex in `parse_one_shot_time` not anchored for multiline (`cron.py:161`)
- No max retry limit on `_call_with_resume_fallback` (`handlers.py`)

## Positive Findings

- All YAML loading uses `yaml.safe_load()` (no arbitrary code execution)
- Subprocess execution uses `create_subprocess_exec` (no `shell=True`)
- `allowed_users` permission check on all handlers
- Process tracking with proper cleanup on shutdown (`cancel_all_processes`)
- Skill `allowed_tools` provides hard permission boundary in Claude Code `-p` mode

## Remediation Priority

1. **Immediate**: Path traversal (#1, #2), name validation (#4, #7)
2. **Short-term**: Rate limiting (#6), environment variable validation (#5), error message sanitization (#13, #20)
3. **Medium-term**: Token encryption (#3), disk quota (#10, #11), download timeout (#14)
4. **Long-term**: Audit logging (#19), config validation (#22), i18n
