"""Tests for cclaw.utils module."""

from __future__ import annotations

from unittest.mock import patch

from cclaw.utils import (
    markdown_to_telegram_html,
    prompt_input,
    prompt_multiline,
    split_message,
)


class TestPromptInput:
    """Tests for prompt_input function."""

    @patch("builtins.input", return_value="hello world")
    def test_prompt_input_basic(self, mock_input: object) -> None:
        result = prompt_input("Enter value:")
        assert result == "hello world"

    @patch("builtins.input", return_value="  spaced  ")
    def test_prompt_input_strips_whitespace(self, mock_input: object) -> None:
        result = prompt_input("Enter value:")
        assert result == "spaced"

    @patch("builtins.input", return_value="custom value")
    def test_prompt_input_with_default_uses_input(self, mock_input: object) -> None:
        result = prompt_input("Enter value:", default="fallback")
        assert result == "custom value"

    @patch("builtins.input", return_value="")
    def test_prompt_input_with_default_uses_default_on_empty(self, mock_input: object) -> None:
        result = prompt_input("Enter value:", default="fallback")
        assert result == "fallback"

    @patch("builtins.input", return_value="   ")
    def test_prompt_input_with_default_uses_default_on_whitespace(self, mock_input: object) -> None:
        result = prompt_input("Enter value:", default="fallback")
        assert result == "fallback"


class TestPromptMultiline:
    """Tests for prompt_multiline function."""

    @patch("builtins.input", side_effect=["line one", "line two", ""])
    def test_prompt_multiline_basic(self, mock_input: object) -> None:
        result = prompt_multiline("Enter text:")
        assert result == "line one\nline two"

    @patch("builtins.input", side_effect=[""])
    def test_prompt_multiline_empty(self, mock_input: object) -> None:
        result = prompt_multiline("Enter text:")
        assert result == ""

    @patch("builtins.input", side_effect=["single line", ""])
    def test_prompt_multiline_single_line(self, mock_input: object) -> None:
        result = prompt_multiline("Enter text:")
        assert result == "single line"


class TestSplitMessage:
    """Tests for split_message function."""

    def test_short_message(self) -> None:
        result = split_message("hello")
        assert result == ["hello"]

    def test_split_at_newline(self) -> None:
        text = "a" * 4000 + "\n" + "b" * 1000
        result = split_message(text, limit=4096)
        assert len(result) == 2


class TestMarkdownToTelegramHtml:
    """Tests for markdown_to_telegram_html function."""

    def test_bold(self) -> None:
        result = markdown_to_telegram_html("**bold text**")
        assert "<b>bold text</b>" in result

    def test_italic(self) -> None:
        result = markdown_to_telegram_html("*italic text*")
        assert "<i>italic text</i>" in result

    def test_inline_code(self) -> None:
        result = markdown_to_telegram_html("`code`")
        assert "<code>code</code>" in result

    def test_heading(self) -> None:
        result = markdown_to_telegram_html("## Heading")
        assert "<b>Heading</b>" in result
