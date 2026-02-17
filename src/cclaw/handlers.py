"""Telegram handler factory for cclaw bots."""

from __future__ import annotations

import asyncio
import logging
from pathlib import Path
from typing import Any

from telegram import BotCommand, Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from cclaw.claude_runner import cancel_process, is_process_running, run_claude
from cclaw.config import DEFAULT_MODEL, VALID_MODELS, is_valid_model, save_bot_config
from cclaw.session import (
    ensure_session,
    list_workspace_files,
    log_conversation,
    reset_all_session,
    reset_session,
)
from cclaw.utils import markdown_to_telegram_html, split_message

logger = logging.getLogger(__name__)

SESSION_LOCKS: dict[str, asyncio.Lock] = {}
MAX_QUEUE_SIZE = 5


def _get_session_lock(key: str) -> asyncio.Lock:
    """Get or create a session lock for the given key."""
    if key not in SESSION_LOCKS:
        SESSION_LOCKS[key] = asyncio.Lock()
    return SESSION_LOCKS[key]


def _is_user_allowed(user_id: int, allowed_users: list[int]) -> bool:
    """Check if user is allowed. Empty list means all users allowed."""
    if not allowed_users:
        return True
    return user_id in allowed_users


def make_handlers(bot_name: str, bot_path: Path, bot_config: dict[str, Any]) -> list:
    """Create Telegram handlers for a bot.

    Returns a list of handler instances to add to the Application.
    """
    allowed_users = bot_config.get("allowed_users", [])
    personality = bot_config.get("personality", "")
    description = bot_config.get("description", "")
    claude_arguments = bot_config.get("claude_args", [])
    command_timeout = bot_config.get("command_timeout", 300)
    current_model = bot_config.get("model", DEFAULT_MODEL)
    attached_skills = bot_config.get("skills", [])

    async def check_authorization(update: Update) -> bool:
        """Check if the user is authorized."""
        if not _is_user_allowed(update.effective_user.id, allowed_users):
            await update.message.reply_text("Unauthorized.")
            return False
        return True

    async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /start command - introduce the bot."""
        if not await check_authorization(update):
            return

        text = (
            f"\U0001f916 *{bot_name}*\n\n"
            f"\U0001f3ad *Personality:* {personality}\n"
            f"\U0001f4bc *Role:* {description}\n\n"
            "\U0001f4ac Send me a message to start chatting!\n"
            "\U00002753 Type /help for available commands."
        )
        await update.message.reply_text(text, parse_mode="Markdown")

    async def help_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /help command."""
        if not await check_authorization(update):
            return

        text = (
            "\U0001f4cb *Available Commands:*\n\n"
            "\U0001f44b /start - Bot introduction\n"
            "\U0001f504 /reset - Clear conversation (keep workspace)\n"
            "\U0001f5d1 /resetall - Delete entire session\n"
            "\U0001f4c2 /files - List workspace files\n"
            "\U0001f4e4 /send - Send workspace file\n"
            "\U0001f4ca /status - Session status\n"
            "\U0001f9e0 /model - Show or change model\n"
            "\U0001f9e9 /skills - List all skills\n"
            "\U0001f9e9 /skill - Manage skills (attach/detach)\n"
            "\u23f0 /cron - Cron job management\n"
            "\U0001f493 /heartbeat - Heartbeat management\n"
            "\u26d4 /cancel - Stop running process\n"
            "\U00002139 /version - Show version\n"
            "\U00002753 /help - Show this message"
        )
        await update.message.reply_text(text, parse_mode="Markdown")

    async def reset_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /reset command."""
        if not await check_authorization(update):
            return

        chat_id = update.effective_chat.id
        reset_session(bot_path, chat_id)
        await update.message.reply_text("\U0001f504 Conversation reset. Workspace files preserved.")

    async def resetall_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /resetall command."""
        if not await check_authorization(update):
            return

        chat_id = update.effective_chat.id
        reset_all_session(bot_path, chat_id)
        await update.message.reply_text("\U0001f5d1 Session completely reset.")

    async def files_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /files command."""
        if not await check_authorization(update):
            return

        chat_id = update.effective_chat.id
        session_directory = ensure_session(bot_path, chat_id)
        files = list_workspace_files(session_directory)

        if not files:
            await update.message.reply_text("\U0001f4c2 No files in workspace.")
            return

        file_list = "\n".join(f"  {f}" for f in files)
        text = f"\U0001f4c2 *Workspace files:*\n```\n{file_list}\n```"
        await update.message.reply_text(text, parse_mode="Markdown")

    async def status_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /status command."""
        if not await check_authorization(update):
            return

        chat_id = update.effective_chat.id
        session_directory = ensure_session(bot_path, chat_id)

        conversation_file = session_directory / "conversation.md"
        if conversation_file.exists():
            size = conversation_file.stat().st_size
            conversation_status = f"{size:,} bytes"
        else:
            conversation_status = "No conversation yet"

        files = list_workspace_files(session_directory)

        text = (
            f"\U0001f4ca *Session Status*\n\n"
            f"\U0001f916 Bot: {bot_name}\n"
            f"\U0001f4ac Chat ID: {chat_id}\n"
            f"\U0001f4dd Conversation: {conversation_status}\n"
            f"\U0001f4c2 Workspace files: {len(files)}"
        )
        await update.message.reply_text(text, parse_mode="Markdown")

    async def send_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /send command - send a workspace file to the user."""
        if not await check_authorization(update):
            return

        chat_id = update.effective_chat.id
        session_directory = ensure_session(bot_path, chat_id)
        workspace = session_directory / "workspace"

        if not context.args:
            files = list_workspace_files(session_directory)
            if not files:
                await update.message.reply_text("\U0001f4c2 No files in workspace.")
                return
            file_list = "\n".join(f"  {f}" for f in files)
            text = f"\U0001f4e4 Usage: `/send filename`\n\nAvailable files:\n```\n{file_list}\n```"
            await update.message.reply_text(text, parse_mode="Markdown")
            return

        filename = " ".join(context.args)
        file_path = workspace / filename

        if not file_path.exists():
            await update.message.reply_text(f"File not found: `{filename}`", parse_mode="Markdown")
            return

        if not file_path.is_file():
            await update.message.reply_text(f"Not a file: `{filename}`", parse_mode="Markdown")
            return

        try:
            await update.message.reply_document(
                document=open(file_path, "rb"),
                filename=file_path.name,
            )
        except Exception as error:
            await update.message.reply_text(f"Failed to send file: {error}")
            logger.error("Failed to send file %s: %s", filename, error)

    async def model_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /model command - show or change the Claude model."""
        nonlocal current_model
        if not await check_authorization(update):
            return

        if not context.args:
            model_list = " / ".join(f"*{m}*" if m == current_model else m for m in VALID_MODELS)
            text = (
                f"\U0001f9e0 Current model: *{current_model}*\n\n"
                f"Available: {model_list}\n"
                "Usage: `/model sonnet`"
            )
            await update.message.reply_text(text, parse_mode="Markdown")
            return

        new_model = context.args[0].lower()
        if not is_valid_model(new_model):
            await update.message.reply_text(
                f"Invalid model: `{new_model}`\nAvailable: {', '.join(VALID_MODELS)}",
                parse_mode="Markdown",
            )
            return

        current_model = new_model
        bot_config["model"] = new_model
        save_bot_config(bot_name, bot_config)
        await update.message.reply_text(
            f"\U0001f9e0 Model changed to *{new_model}*", parse_mode="Markdown"
        )

    async def cancel_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /cancel command - stop running Claude Code process."""
        if not await check_authorization(update):
            return

        chat_id = update.effective_chat.id
        session_key = f"{bot_name}:{chat_id}"

        if not is_process_running(session_key):
            await update.message.reply_text("No running process to cancel.")
            return

        cancelled = cancel_process(session_key)
        if cancelled:
            await update.message.reply_text("\u26d4 Execution cancelled.")
        else:
            await update.message.reply_text("No running process to cancel.")

    async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle regular text messages - forward to Claude Code."""
        if not await check_authorization(update):
            return

        chat_id = update.effective_chat.id
        user_message = update.message.text
        lock_key = f"{bot_name}:{chat_id}"
        lock = _get_session_lock(lock_key)

        if lock.locked():
            await update.message.reply_text(
                "\U0001f4e5 Message queued. Processing previous request..."
            )

        async with lock:
            session_directory = ensure_session(bot_path, chat_id)
            log_conversation(session_directory, "user", user_message)

            async def send_typing_periodically() -> None:
                """Send typing action every 4 seconds until cancelled."""
                try:
                    while True:
                        await update.message.chat.send_action("typing")
                        await asyncio.sleep(4)
                except asyncio.CancelledError:
                    pass

            typing_task = asyncio.create_task(send_typing_periodically())

            try:
                response = await run_claude(
                    working_directory=str(session_directory),
                    message=user_message,
                    extra_arguments=claude_arguments if claude_arguments else None,
                    timeout=command_timeout,
                    session_key=lock_key,
                    model=current_model,
                    skill_names=attached_skills if attached_skills else None,
                )
            except asyncio.CancelledError:
                response = "\u26d4 Execution was cancelled."
                logger.info("Claude cancelled for chat %d", chat_id)
            except TimeoutError:
                response = "Request timed out. Please try a shorter request."
                logger.error("Claude timed out for chat %d", chat_id)
            except RuntimeError as error:
                response = f"Error: {error}"
                logger.error("Claude error for chat %d: %s", chat_id, error)
            finally:
                typing_task.cancel()

            log_conversation(session_directory, "assistant", response)

            html_response = markdown_to_telegram_html(response)
            chunks = split_message(html_response)
            for chunk in chunks:
                try:
                    await update.message.reply_text(chunk, parse_mode="HTML")
                except Exception:
                    await update.message.reply_text(chunk)

    async def version_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /version command."""
        if not await check_authorization(update):
            return

        from cclaw import __version__

        await update.message.reply_text(f"\U00002139 cclaw v{__version__}")

    async def file_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle photo/document messages - download to workspace and forward to Claude."""
        if not await check_authorization(update):
            return

        chat_id = update.effective_chat.id
        lock_key = f"{bot_name}:{chat_id}"
        lock = _get_session_lock(lock_key)

        if lock.locked():
            await update.message.reply_text(
                "\U0001f4e5 Message queued. Processing previous request..."
            )

        async with lock:
            session_dir = ensure_session(bot_path, chat_id)
            workspace = session_dir / "workspace"

            # Determine file to download
            if update.message.photo:
                photo = update.message.photo[-1]  # largest size
                file = await photo.get_file()
                extension = ".jpg"
                filename = f"photo_{photo.file_unique_id}{extension}"
            elif update.message.document:
                document = update.message.document
                file = await document.get_file()
                filename = document.file_name or f"file_{document.file_unique_id}"
            else:
                return

            file_path = workspace / filename
            await file.download_to_drive(str(file_path))

            caption = update.message.caption or ""
            if caption:
                prompt = f"{caption}\n\nFile: {file_path}"
            else:
                prompt = f"I sent a file: {file_path}"

            log_conversation(session_dir, "user", f"[file: {filename}] {caption}")

            async def send_typing_periodically() -> None:
                try:
                    while True:
                        await update.message.chat.send_action("typing")
                        await asyncio.sleep(4)
                except asyncio.CancelledError:
                    pass

            typing_task = asyncio.create_task(send_typing_periodically())

            try:
                response = await run_claude(
                    working_directory=str(session_dir),
                    message=prompt,
                    extra_arguments=claude_arguments if claude_arguments else None,
                    timeout=command_timeout,
                    session_key=lock_key,
                    model=current_model,
                    skill_names=attached_skills if attached_skills else None,
                )
            except asyncio.CancelledError:
                response = "\u26d4 Execution was cancelled."
                logger.info("Claude cancelled for chat %d", chat_id)
            except TimeoutError:
                response = "Request timed out. Please try a shorter request."
                logger.error("Claude timed out for chat %d", chat_id)
            except RuntimeError as error:
                response = f"Error: {error}"
                logger.error("Claude error for chat %d: %s", chat_id, error)
            finally:
                typing_task.cancel()

            log_conversation(session_dir, "assistant", response)

            html_response = markdown_to_telegram_html(response)
            chunks = split_message(html_response)
            for chunk in chunks:
                try:
                    await update.message.reply_text(chunk, parse_mode="HTML")
                except Exception:
                    await update.message.reply_text(chunk)

    async def skills_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /skills command - list all available skills."""
        if not await check_authorization(update):
            return

        from cclaw.skill import bots_using_skill, list_skills

        all_skills = list_skills()

        if not all_skills:
            await update.message.reply_text("\U0001f9e9 No skills available.")
            return

        lines = ["\U0001f9e9 *All Skills:*\n"]
        for skill in all_skills:
            skill_type_display = skill["type"] or "markdown"
            status_icon = "\u2705" if skill["status"] == "active" else "\U0001f6d1"
            connected_bots = bots_using_skill(skill["name"])
            attached_label = f" \u2190 {', '.join(connected_bots)}" if connected_bots else ""
            lines.append(f"{status_icon} `{skill['name']}` ({skill_type_display}){attached_label}")

        await update.message.reply_text("\n".join(lines), parse_mode="Markdown")

    async def cron_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /cron command - list or run cron jobs."""
        if not await check_authorization(update):
            return

        from cclaw.cron import execute_cron_job, get_cron_job, list_cron_jobs, next_run_time

        if not context.args:
            text = (
                "\u23f0 *Cron Commands:*\n\n"
                "`/cron list` - Show cron jobs\n"
                "`/cron run <name>` - Run a job now"
            )
            await update.message.reply_text(text, parse_mode="Markdown")
            return

        subcommand = context.args[0].lower()

        if subcommand == "list":
            jobs = list_cron_jobs(bot_name)
            if not jobs:
                await update.message.reply_text("\u23f0 No cron jobs configured.")
                return

            lines = ["\u23f0 *Cron Jobs:*\n"]
            for job in jobs:
                enabled = job.get("enabled", True)
                status_icon = "\u2705" if enabled else "\U0001f6d1"
                schedule_display = job.get("schedule") or f"at: {job.get('at', 'N/A')}"
                next_time = next_run_time(job) if enabled else None
                next_display = next_time.strftime("%m-%d %H:%M") if next_time else "-"
                message_preview = job.get("message", "")[:30]
                lines.append(
                    f"{status_icon} `{job['name']}` ({schedule_display})\n"
                    f"   Next: {next_display} | {message_preview}"
                )
            await update.message.reply_text("\n".join(lines), parse_mode="Markdown")

        elif subcommand == "run":
            if len(context.args) < 2:
                await update.message.reply_text("Usage: `/cron run <name>`", parse_mode="Markdown")
                return

            job_name = context.args[1]
            cron_job = get_cron_job(bot_name, job_name)
            if not cron_job:
                await update.message.reply_text(f"Job '{job_name}' not found.")
                return

            await update.message.reply_text(f"\u23f0 Running job '{job_name}'...")

            async def send_typing_periodically() -> None:
                try:
                    while True:
                        await update.message.chat.send_action("typing")
                        await asyncio.sleep(4)
                except asyncio.CancelledError:
                    pass

            typing_task = asyncio.create_task(send_typing_periodically())

            try:
                await execute_cron_job(
                    bot_name=bot_name,
                    job=cron_job,
                    bot_config=bot_config,
                    send_message_callback=context.bot.send_message,
                )
            except Exception as error:
                await update.message.reply_text(f"Job failed: {error}")
            finally:
                typing_task.cancel()

        else:
            await update.message.reply_text(
                "Unknown subcommand. Use: list, run",
            )

    async def skill_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /skill command - manage skill attachments."""
        nonlocal attached_skills
        if not await check_authorization(update):
            return

        if not context.args:
            text = (
                "\U0001f9e9 *Skill Commands:*\n\n"
                "`/skill list` - Show attached skills\n"
                "`/skill attach <name>` - Attach a skill\n"
                "`/skill detach <name>` - Detach a skill"
            )
            await update.message.reply_text(text, parse_mode="Markdown")
            return

        subcommand = context.args[0].lower()

        if subcommand == "list":
            if not attached_skills:
                await update.message.reply_text("\U0001f9e9 No skills attached.")
                return
            skill_list = "\n".join(f"  - {s}" for s in attached_skills)
            await update.message.reply_text(
                f"\U0001f9e9 *Attached Skills:*\n```\n{skill_list}\n```",
                parse_mode="Markdown",
            )

        elif subcommand == "attach":
            if len(context.args) < 2:
                await update.message.reply_text(
                    "Usage: `/skill attach <name>`", parse_mode="Markdown"
                )
                return

            from cclaw.skill import attach_skill_to_bot, is_skill, skill_status

            skill_name = context.args[1]
            if not is_skill(skill_name):
                await update.message.reply_text(f"Skill '{skill_name}' not found.")
                return

            status = skill_status(skill_name)
            if status == "inactive":
                await update.message.reply_text(
                    f"Skill '{skill_name}' is inactive. "
                    f"Run `cclaw skill setup {skill_name}` first.",
                    parse_mode="Markdown",
                )
                return

            if skill_name in attached_skills:
                await update.message.reply_text(f"Skill '{skill_name}' is already attached.")
                return

            attach_skill_to_bot(bot_name, skill_name)
            bot_config.setdefault("skills", [])
            if skill_name not in bot_config["skills"]:
                bot_config["skills"].append(skill_name)
            attached_skills = bot_config["skills"]
            await update.message.reply_text(f"\U0001f9e9 Skill '{skill_name}' attached.")

        elif subcommand == "detach":
            if len(context.args) < 2:
                await update.message.reply_text(
                    "Usage: `/skill detach <name>`", parse_mode="Markdown"
                )
                return

            from cclaw.skill import detach_skill_from_bot

            skill_name = context.args[1]
            if skill_name not in attached_skills:
                await update.message.reply_text(f"Skill '{skill_name}' is not attached.")
                return

            detach_skill_from_bot(bot_name, skill_name)
            if skill_name in bot_config.get("skills", []):
                bot_config["skills"].remove(skill_name)
            attached_skills = bot_config.get("skills", [])
            await update.message.reply_text(f"\U0001f9e9 Skill '{skill_name}' detached.")

        else:
            await update.message.reply_text(
                "Unknown subcommand. Use: list, attach, detach",
            )

    async def heartbeat_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /heartbeat command - manage heartbeat settings."""
        if not await check_authorization(update):
            return

        from cclaw.heartbeat import (
            disable_heartbeat,
            enable_heartbeat,
            execute_heartbeat,
            get_heartbeat_config,
        )

        if not context.args:
            heartbeat_config = get_heartbeat_config(bot_name)
            enabled = heartbeat_config.get("enabled", False)
            interval = heartbeat_config.get("interval_minutes", 30)
            active_hours = heartbeat_config.get("active_hours", {})
            start = active_hours.get("start", "07:00")
            end = active_hours.get("end", "23:00")
            status_text = "on" if enabled else "off"
            text = (
                f"\U0001f493 *Heartbeat Status*\n\n"
                f"Status: *{status_text}*\n"
                f"Interval: {interval}m\n"
                f"Active hours: {start} - {end}\n\n"
                "`/heartbeat on` - Enable\n"
                "`/heartbeat off` - Disable\n"
                "`/heartbeat run` - Run now"
            )
            await update.message.reply_text(text, parse_mode="Markdown")
            return

        subcommand = context.args[0].lower()

        if subcommand == "on":
            if enable_heartbeat(bot_name):
                await update.message.reply_text("\U0001f493 Heartbeat enabled.")
            else:
                await update.message.reply_text("Failed to enable heartbeat.")

        elif subcommand == "off":
            if disable_heartbeat(bot_name):
                await update.message.reply_text("\U0001f493 Heartbeat disabled.")
            else:
                await update.message.reply_text("Failed to disable heartbeat.")

        elif subcommand == "run":
            await update.message.reply_text("\U0001f493 Running heartbeat check...")

            async def send_typing_periodically() -> None:
                try:
                    while True:
                        await update.message.chat.send_action("typing")
                        await asyncio.sleep(4)
                except asyncio.CancelledError:
                    pass

            typing_task = asyncio.create_task(send_typing_periodically())

            try:
                await execute_heartbeat(
                    bot_name=bot_name,
                    bot_config=bot_config,
                    send_message_callback=context.bot.send_message,
                )
                await update.message.reply_text("\U0001f493 Heartbeat check completed.")
            except Exception as error:
                await update.message.reply_text(f"Heartbeat failed: {error}")
            finally:
                typing_task.cancel()

        else:
            await update.message.reply_text(
                "Unknown subcommand. Use: on, off, run",
            )

    handlers = [
        CommandHandler("start", start_handler),
        CommandHandler("help", help_handler),
        CommandHandler("reset", reset_handler),
        CommandHandler("resetall", resetall_handler),
        CommandHandler("files", files_handler),
        CommandHandler("send", send_handler),
        CommandHandler("status", status_handler),
        CommandHandler("model", model_handler),
        CommandHandler("version", version_handler),
        CommandHandler("cancel", cancel_handler),
        CommandHandler("skills", skills_handler),
        CommandHandler("skill", skill_handler),
        CommandHandler("cron", cron_handler),
        CommandHandler("heartbeat", heartbeat_handler),
        MessageHandler(filters.PHOTO | filters.Document.ALL, file_handler),
        MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler),
    ]

    return handlers


BOT_COMMANDS = [
    BotCommand("start", "\U0001f44b Bot introduction"),
    BotCommand("reset", "\U0001f504 Clear conversation"),
    BotCommand("resetall", "\U0001f5d1 Delete entire session"),
    BotCommand("files", "\U0001f4c2 List workspace files"),
    BotCommand("send", "\U0001f4e4 Send workspace file"),
    BotCommand("status", "\U0001f4ca Session status"),
    BotCommand("model", "\U0001f9e0 Show or change model"),
    BotCommand("skills", "\U0001f9e9 List all skills"),
    BotCommand("skill", "\U0001f9e9 Manage skills"),
    BotCommand("cron", "\u23f0 Cron job management"),
    BotCommand("heartbeat", "\U0001f493 Heartbeat management"),
    BotCommand("cancel", "\u26d4 Stop running process"),
    BotCommand("version", "\U00002139 Show version"),
    BotCommand("help", "\U00002753 Show commands"),
]


async def set_bot_commands(application: Application) -> None:
    """Register slash commands with Telegram (called via post_init)."""
    await application.bot.set_my_commands(BOT_COMMANDS)
