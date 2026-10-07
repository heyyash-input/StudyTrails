import sys
from io import StringIO

import pytest
from rich.console import Console

from study_agent.ui import confirm, show_answer


@pytest.mark.parametrize(
    ("answer", "expected"), [("y", True), ("YES", True), ("n", False), ("No", False), ("", False)]
)
def test_confirmation_keeps_choices_visible_and_accepts_answers(monkeypatch, answer, expected):
    output = StringIO()
    monkeypatch.setattr(sys, "stdin", StringIO(answer + "\n"))
    assert confirm(Console(file=output), "Continue?") is expected
    assert "Continue? [y/n] (Enter = no):" in output.getvalue()


def test_markdown_reply_formats_text_but_preserves_code_and_citations():
    output = StringIO()
    show_answer(
        Console(file=output, width=70, force_terminal=False),
        "## Loops\n\n**Repeat** a task. [loops.md:3]\n\n"
        "```python\nfor i in range(3):\n    print(i)\n```",
    )
    text = output.getvalue()
    assert "Coach" in text and "Loops" in text
    assert "**Repeat**" not in text and "Repeat" in text
    assert "```" not in text
    assert "[loops.md:3]" in text
    assert "for i in range(3):" in text and "    print(i)" in text
