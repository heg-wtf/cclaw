"""Evaluation tests for cron natural language parsing quality.

These tests call the real Claude API and are NOT part of normal CI.
Run manually when modifying the parsing prompt:

    uv run pytest tests/evaluation/test_cron_parsing_quality.py -v

"""

from __future__ import annotations

import re

import pytest

from cclaw.cron import parse_natural_language_schedule

TIMEZONE = "Asia/Seoul"

EVALUATION_CASES = [
    # --- Recurring (Korean) ---
    ("매일 아침 9시에 이메일 요약해줘", "recurring", "0 9 * * *"),
    ("평일 오후 6시에 뉴스 정리", "recurring", "0 18 * * 1-5"),
    ("매주 월요일 10시에 주간 리포트", "recurring", "0 10 * * 1"),
    ("매월 1일 오전 10시에 월간 보고", "recurring", "0 10 1 * *"),
    # --- Recurring (English) ---
    ("every morning at 9am summarize emails", "recurring", "0 9 * * *"),
    ("every weekday at 6pm news summary", "recurring", "0 18 * * 1-5"),
    ("every Monday at 10am weekly report", "recurring", "0 10 * * 1"),
    ("every 1st of the month at 10am monthly report", "recurring", "0 10 1 * *"),
    # --- Recurring (Japanese) ---
    ("毎日朝9時にメールをまとめて", "recurring", "0 9 * * *"),
    ("平日の午後6時にニュースまとめ", "recurring", "0 18 * * 1-5"),
    # --- Oneshot (Korean) ---
    ("30분 뒤에 회의 알림", "oneshot", None),
    ("내일 오후 2시에 보고서 확인", "oneshot", None),
    ("다음 주 화요일 3시에 미팅 준비", "oneshot", None),
    # --- Oneshot (English) ---
    ("in 30 minutes remind me about the meeting", "oneshot", None),
    ("tomorrow at 2pm check the report", "oneshot", None),
    ("next Tuesday at 3pm prepare for meeting", "oneshot", None),
]


def normalize_cron_weekday(expression: str) -> str:
    """Normalize equivalent cron weekday representations."""
    # 0-6 and 1-5 vs MON-FRI etc. - just compare as-is for now
    # Handle * * * * 0-6 == * * * * *
    return expression.replace("0-6", "*").replace("0,1,2,3,4,5,6", "*")


@pytest.mark.evaluation
@pytest.mark.parametrize(
    "user_input,expected_type,expected_schedule",
    EVALUATION_CASES,
    ids=[case[0][:30] for case in EVALUATION_CASES],
)
@pytest.mark.asyncio
async def test_cron_parsing_quality(
    user_input: str,
    expected_type: str,
    expected_schedule: str | None,
) -> None:
    """Evaluate natural language cron parsing quality with real Claude."""
    result = await parse_natural_language_schedule(user_input, TIMEZONE)

    # Type must be correct (100% accuracy required)
    assert result["type"] == expected_type, (
        f"Type mismatch for '{user_input}': expected {expected_type}, got {result['type']}"
    )

    # Schedule must match for recurring jobs
    if expected_schedule is not None:
        actual = normalize_cron_weekday(result["schedule"])
        expected = normalize_cron_weekday(expected_schedule)
        assert actual == expected, (
            f"Schedule mismatch for '{user_input}': "
            f"expected {expected_schedule}, got {result['schedule']}"
        )

    # Oneshot must have valid ISO datetime
    if expected_type == "oneshot":
        assert "at" in result, f"Missing 'at' for oneshot: '{user_input}'"
        assert re.match(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}", result["at"]), (
            f"Invalid ISO datetime: {result['at']}"
        )

    # Message must be non-empty
    assert result["message"].strip(), f"Empty message for '{user_input}'"

    # Name must be kebab-case English
    assert re.match(r"^[a-z0-9]+(-[a-z0-9]+)*$", result["name"]), (
        f"Invalid name format: {result['name']}"
    )
