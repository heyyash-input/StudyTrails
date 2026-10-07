"""Shared terminal prompts and readable coach output."""

from rich.console import Console
from rich.markdown import Markdown
from rich.text import Text


def confirm(console: Console, question: str) -> bool:
    while True:
        answer = console.input(Text(f"{question} [y/n] (Enter = no): ")).strip().lower()
        if answer in {"y", "yes"}:
            return True
        if answer in {"", "n", "no"}:
            return False
        console.print("Please enter y for yes or n for no.")


def show_answer(console: Console, answer: str) -> None:
    console.print("\nCoach", style="bold cyan")
    console.print(Markdown(answer, hyperlinks=False), width=min(console.width, 100))
    console.print()
