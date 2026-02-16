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

from cclaw.claude_runner import run_claude
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
            "\U0001f4ca /status - Session status\n"
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

    async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle regular text messages - forward to Claude Code."""
        if not await check_authorization(update):
            return

        chat_id = update.effective_chat.id
        user_message = update.message.text
        lock_key = f"{bot_name}:{chat_id}"
        lock = _get_session_lock(lock_key)

        if lock.locked():
            await update.message.reply_text("Processing a previous message. Please wait...")
            return

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
                )
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
            await update.message.reply_text("Processing a previous message. Please wait...")
            return

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
                )
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

    handlers = [
        CommandHandler("start", start_handler),
        CommandHandler("help", help_handler),
        CommandHandler("reset", reset_handler),
        CommandHandler("resetall", resetall_handler),
        CommandHandler("files", files_handler),
        CommandHandler("status", status_handler),
        CommandHandler("version", version_handler),
        MessageHandler(filters.PHOTO | filters.Document.ALL, file_handler),
        MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler),
    ]

    return handlers


BOT_COMMANDS = [
    BotCommand("start", "\U0001f44b Bot introduction"),
    BotCommand("reset", "\U0001f504 Clear conversation"),
    BotCommand("resetall", "\U0001f5d1 Delete entire session"),
    BotCommand("files", "\U0001f4c2 List workspace files"),
    BotCommand("status", "\U0001f4ca Session status"),
    BotCommand("version", "\U00002139 Show version"),
    BotCommand("help", "\U00002753 Show commands"),
]


async def set_bot_commands(application: Application) -> None:
    """Register slash commands with Telegram (called via post_init)."""
    await application.bot.set_my_commands(BOT_COMMANDS)
