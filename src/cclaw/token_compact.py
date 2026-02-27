"""Token compact — compress MD files to save tokens."""

from __future__ import annotations

import logging
import tempfile
from dataclasses import dataclass
from pathlib import Path

from cclaw.config import bot_directory, load_bot_config

logger = logging.getLogger(__name__)

COMPACT_PROMPT = """You are a content compressor. Compress the following {document_type} document.

Rules:
1. PRESERVE: safety rules, command syntax, URLs, IDs, coordinates, file paths, key facts/data
2. REMOVE: redundant entries, duplicate info, verbose descriptions
3. MERGE: related items saying the same thing
4. SHORTEN: descriptions to concise bullets
5. Keep Markdown structure. Output ONLY the compressed document.
6. If already concise, return unchanged.

---
{content}"""

DOCUMENT_TYPE_MEMORY = "Bot long-term memory (facts, preferences, user data)"
DOCUMENT_TYPE_SKILL = "AI assistant skill instructions (tool usage, commands)"
DOCUMENT_TYPE_HEARTBEAT = "Periodic health check checklist"


def estimate_token_count(text: str) -> int:
    """Estimate token count using chars // 4 heuristic. For relative comparison."""
    return max(1, len(text) // 4)


@dataclass
class CompactTarget:
    """A file eligible for compaction."""

    label: str
    file_path: Path
    content: str
    line_count: int
    token_count: int
    document_type: str


@dataclass
class CompactResult:
    """Result of compacting a single target."""

    target: CompactTarget
    compacted_content: str = ""
    compacted_lines: int = 0
    compacted_tokens: int = 0
    error: str | None = None

    @property
    def savings_percentage(self) -> float:
        """Calculate percentage of tokens saved."""
        if self.target.token_count == 0:
            return 0.0
        saved = self.target.token_count - self.compacted_tokens
        return (saved / self.target.token_count) * 100


def collect_compact_targets(bot_name: str) -> list[CompactTarget]:
    """Collect all files eligible for compaction.

    Targets: MEMORY.md, user-created SKILL.md (not builtins), HEARTBEAT.md.
    """
    from cclaw.builtin_skills import is_builtin_skill
    from cclaw.skill import skill_directory

    targets: list[CompactTarget] = []

    bot_path = bot_directory(bot_name)
    bot_config = load_bot_config(bot_name)
    if not bot_config:
        return targets

    # 1. MEMORY.md
    memory_path = bot_path / "MEMORY.md"
    if memory_path.exists():
        content = memory_path.read_text()
        if content.strip():
            targets.append(
                CompactTarget(
                    label="MEMORY.md",
                    file_path=memory_path,
                    content=content,
                    line_count=len(content.splitlines()),
                    token_count=estimate_token_count(content),
                    document_type=DOCUMENT_TYPE_MEMORY,
                )
            )

    # 2. User-created SKILL.md (exclude builtins)
    for skill_name in bot_config.get("skills", []):
        if is_builtin_skill(skill_name):
            continue
        skill_md_path = skill_directory(skill_name) / "SKILL.md"
        if skill_md_path.exists():
            content = skill_md_path.read_text()
            if content.strip():
                targets.append(
                    CompactTarget(
                        label=f"Skill: {skill_name}",
                        file_path=skill_md_path,
                        content=content,
                        line_count=len(content.splitlines()),
                        token_count=estimate_token_count(content),
                        document_type=DOCUMENT_TYPE_SKILL,
                    )
                )

    # 3. HEARTBEAT.md
    heartbeat_path = bot_path / "heartbeat_sessions" / "HEARTBEAT.md"
    if heartbeat_path.exists():
        content = heartbeat_path.read_text()
        if content.strip():
            targets.append(
                CompactTarget(
                    label="HEARTBEAT.md",
                    file_path=heartbeat_path,
                    content=content,
                    line_count=len(content.splitlines()),
                    token_count=estimate_token_count(content),
                    document_type=DOCUMENT_TYPE_HEARTBEAT,
                )
            )

    return targets


async def compact_content(
    content: str,
    document_type: str,
    working_directory: str,
    model: str = "sonnet",
    timeout: int = 120,
) -> str:
    """Compress a single document using Claude Code.

    Returns the compacted content string.
    """
    from cclaw.claude_runner import run_claude

    prompt = COMPACT_PROMPT.format(document_type=document_type, content=content)

    result = await run_claude(
        working_directory=working_directory,
        message=prompt,
        model=model,
        timeout=timeout,
    )

    return result.strip()


async def run_compact(bot_name: str, model: str = "sonnet") -> list[CompactResult]:
    """Run compaction on all eligible targets for a bot.

    Processes targets sequentially. Individual failures do not stop remaining targets.
    """
    targets = collect_compact_targets(bot_name)
    results: list[CompactResult] = []

    for target in targets:
        try:
            with tempfile.TemporaryDirectory() as temporary_directory:
                compacted = await compact_content(
                    content=target.content,
                    document_type=target.document_type,
                    working_directory=temporary_directory,
                    model=model,
                )
            results.append(
                CompactResult(
                    target=target,
                    compacted_content=compacted,
                    compacted_lines=len(compacted.splitlines()),
                    compacted_tokens=estimate_token_count(compacted),
                )
            )
        except Exception as error:
            logger.error("Failed to compact %s: %s", target.label, error)
            results.append(
                CompactResult(
                    target=target,
                    error=str(error),
                )
            )

    return results


def format_compact_report(bot_name: str, results: list[CompactResult]) -> str:
    """Generate a human-readable compaction report."""
    lines = [f"\U0001f4e6 Token Compact: {bot_name}", ""]

    total_before = 0
    total_after = 0

    for result in results:
        if result.error:
            lines.append(f"\u274c {result.target.label}")
            lines.append(f"  Error: {result.error}")
            lines.append("")
            continue

        before_tokens = result.target.token_count
        after_tokens = result.compacted_tokens
        saved_tokens = before_tokens - after_tokens
        percentage = result.savings_percentage

        total_before += before_tokens
        total_after += after_tokens

        if "MEMORY" in result.target.label:
            icon = "\U0001f4dd"
        elif "Skill" in result.target.label:
            icon = "\U0001f9e9"
        else:
            icon = "\U0001f493"

        lines.append(f"{icon} {result.target.label}")
        lines.append(f"  Before: {result.target.line_count} lines, ~{before_tokens:,} tokens")
        lines.append(f"  After:  {result.compacted_lines} lines, ~{after_tokens:,} tokens")
        lines.append(f"  Saved:  ~{saved_tokens:,} tokens ({percentage:.0f}%)")
        lines.append("")

    if total_before > 0:
        total_saved = total_before - total_after
        total_percentage = (total_saved / total_before) * 100
        lines.append(f"Total saved: ~{total_saved:,} tokens ({total_percentage:.0f}%)")
    else:
        lines.append("Total saved: 0 tokens")

    return "\n".join(lines)


def save_compact_results(results: list[CompactResult]) -> None:
    """Save successfully compacted content back to original files.

    Only writes results that have no error.
    """
    for result in results:
        if result.error:
            continue
        result.target.file_path.write_text(result.compacted_content)
        logger.info("Saved compacted %s (%s)", result.target.label, result.target.file_path)
