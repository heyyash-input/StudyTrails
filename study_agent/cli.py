"""Terminal entry point. User answers, not model claims, drive saved results."""

import argparse
import sqlite3

from openai import APIConnectionError, APIError, APIStatusError, AuthenticationError, RateLimitError
from rich.console import Console

from .agent import StudyAgent
from .config import Settings
from .demo import prepare_demo
from .notes import search_notes
from .storage import Store
from .tools import StudyTools

console = Console(markup=False, highlight=False)


def trace(name: str) -> None:
    console.print(f"  Tool: {name}", style="dim")


def show_scores(store: Store) -> None:
    scores = store.get_scores()
    if not scores["completed_quizzes"]:
        console.print("No completed quizzes yet. Take a quiz to begin tracking progress.")
        return
    console.print(f"\nCompleted quizzes: {scores['completed_quizzes']}", style="bold cyan")
    for topic in scores["topics"]:
        console.print(
            f"  {topic['topic']}: {topic['percentage']}% "
            f"({topic['correct']}/{topic['total']} correct across {topic['attempts']} quizzes)"
        )
    console.print("Topics are shown from lowest to highest overall score.")


def take_quiz(store: Store, quiz_id: str) -> None:
    quiz = store.get_quiz(quiz_id)
    if store.is_completed(quiz_id):
        raise ValueError("This quiz is already completed. Request a new one to practise again.")
    console.print(f"\n{quiz.topic.title()} | {quiz.difficulty} | Quiz {quiz_id}", style="bold cyan")
    console.print("Choose A, B, C, or D. Enter Q to leave without submitting.")
    answers = []
    for number, question in enumerate(quiz.questions, start=1):
        console.print(f"\n{number}. {question.prompt}")
        for letter, option in zip("ABCD", question.options, strict=True):
            console.print(f"  {letter}. {option}")
        while True:
            answer = console.input("Your answer: ").strip().upper()
            if answer == "Q":
                mode = " --demo" if store.path.name == "demo.sqlite3" else ""
                console.print(
                    "Nothing submitted. Resume with: "
                    f"uv run python -m study_agent quiz {quiz_id}{mode}"
                )
                return
            if answer in {"A", "B", "C", "D"}:
                answers.append("ABCD".index(answer))
                break
            console.print("Please enter A, B, C, D, or Q.")
    result = store.save_result(quiz_id, answers)
    console.print(
        f"\nSaved result: {result['score']}/{result['total']} ({result['percentage']}%)",
        style="bold green",
    )
    for number, (question, correct) in enumerate(
        zip(quiz.questions, result["correct"], strict=True), start=1
    ):
        status = "Correct" if correct else "Review"
        letter = "ABCD"[question.correct_index]
        console.print(
            f"\n{number}. {status} — answer {letter}: {question.options[question.correct_index]}"
        )
        console.print(question.explanation)


def offer_quizzes(tools: StudyTools) -> None:
    for quiz_id in tools.created_quizzes:
        if tools.store.is_completed(quiz_id):
            continue
        console.print(f"Quiz ready: {quiz_id}")
        if console.input("Take it now? [y/N]: ").strip().lower() in {"y", "yes"}:
            take_quiz(tools.store, quiz_id)
        else:
            console.print(f"Saved for later: uv run python -m study_agent quiz {quiz_id}")


def describe_error(exc: Exception) -> str:
    # Do not print raw provider responses, request headers, or API keys.
    if isinstance(exc, AuthenticationError):
        return "API authentication failed. Check GROQ_API_KEY in your local .env file."
    if isinstance(exc, RateLimitError):
        return (
            "API quota or rate limit reached. Wait for your Groq Free plan limit "
            "to reset; check your Groq limits."
        )
    if isinstance(exc, APIConnectionError):
        return "Could not reach the API. Check your network, then try again."
    if isinstance(exc, APIStatusError):
        if exc.status_code == 404 and exc.code == "model_not_found":
            return (
                "Groq cannot access the configured model. Update GROQ_MODEL in .env "
                "to an available model (default: openai/gpt-oss-120b), then restart the app. "
                f"Request ID: {exc.request_id or 'unavailable'}"
            )
        return (
            f"The API returned HTTP {exc.status_code}. Check model access and configuration. "
            f"Request ID: {exc.request_id or 'unavailable'}"
        )
    if isinstance(exc, APIError):
        return "The API request failed. Check your connection and model configuration."
    return str(exc)


def chat(settings: Settings, tools: StudyTools) -> None:
    agent = StudyAgent(settings, tools, trace)
    console.print("\nStudyTrail | live AI", style="bold cyan")
    console.print("Try: Help me practise Python loops with 3 questions.")
    console.print(
        "Commands: /scores, /pending, /quit. "
        "Each request uses Groq API quota; Free plan limits apply."
    )
    while True:
        goal = console.input("\nYou: ").strip()
        if goal in {"/quit", "/exit"}:
            return
        if goal == "/scores":
            show_scores(tools.store)
            continue
        if goal == "/pending":
            show_pending(tools.store)
            continue
        if not goal:
            continue
        try:
            with console.status("Coach is working..."):
                answer = agent.run(goal)
            console.print(f"\nCoach: {answer}")
            offer_quizzes(tools)
        except (ValueError, RuntimeError, APIError) as exc:
            console.print(f"Error: {describe_error(exc)}", style="red")
            if tools.created_quizzes:
                console.print("A quiz was saved before the error; use /pending to find it.")


def show_pending(store: Store) -> None:
    pending = store.pending_quizzes()
    if not pending:
        console.print("No pending quizzes.")
    for quiz in pending:
        console.print(f"  {quiz['id']} — {quiz['topic']}")
    if pending:
        mode = " --demo" if store.path.name == "demo.sqlite3" else ""
        console.print(f"Take one with: uv run python -m study_agent quiz QUIZ_ID{mode}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="A personal Python study coach.")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("demo", help="Try a fixed offline quiz; no API key or network required.")
    commands.add_parser("chat", help="Start the live tool-using AI coach.")
    ask = commands.add_parser("ask", help="Send one study request to the live AI coach.")
    ask.add_argument("goal")
    commands.add_parser("doctor", help="Check local configuration without contacting the API.")
    for name, description in [
        ("scores", "Show saved quiz results."),
        ("pending", "List uncompleted quizzes."),
        ("quiz", "Take a previously generated quiz."),
    ]:
        command = commands.add_parser(name, help=description)
        if name == "quiz":
            command.add_argument("quiz_id")
        command.add_argument("--demo", action="store_true", help="Use the separate demo database.")
    notes = commands.add_parser("notes", help="Search local notes without an API call.")
    notes.add_argument("query")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    settings = Settings.load()
    try:
        if args.command == "doctor":
            console.print(f"Project: {settings.root}")
            console.print("Provider: Groq")
            console.print(f"Model: {settings.model or '(missing)'}")
            console.print(
                f"API key: {'configured (not verified)' if settings.api_key else 'not configured'}"
            )
            console.print(f"Notes: {settings.root / 'notes'}")
            console.print("Offline demo is available. This check does not contact Groq.")
            return 0
        if args.command == "notes":
            passages = search_notes(settings.root / "notes", args.query)
            for passage in passages:
                console.print(f"\n[{passage['source']}:{passage['line']}]\n{passage['text']}")
            if not passages:
                console.print("No matching notes. Try a specific topic such as loops or functions.")
            return 0
        if args.command in {"chat", "ask"}:
            settings.require_api()
        demo_mode = args.command == "demo" or getattr(args, "demo", False)
        db_name = "demo.sqlite3" if demo_mode else "study.sqlite3"
        store = Store(settings.root / "data" / db_name)
        tools = StudyTools(store, settings.root / "notes")
        if demo_mode:
            console.print(
                "OFFLINE DEMO — fixed content, no AI calls; demo scores are separate.",
                style="yellow",
            )
        match args.command:
            case "demo":
                quiz_id = prepare_demo(tools, trace)
                take_quiz(store, quiz_id)
                console.print("\nNext: configure .env, then run: uv run python -m study_agent chat")
            case "chat":
                chat(settings, tools)
            case "ask":
                answer = StudyAgent(settings, tools, trace).run(args.goal)
                console.print(f"\nCoach: {answer}")
                offer_quizzes(tools)
            case "scores":
                show_scores(store)
            case "pending":
                show_pending(store)
            case "quiz":
                take_quiz(store, args.quiz_id)
        return 0
    except (ValueError, RuntimeError, APIError, OSError, sqlite3.Error) as exc:
        console.print(f"Error: {describe_error(exc)}", style="red")
        return 1
    except (KeyboardInterrupt, EOFError):
        console.print("\nSession ended. Completed quizzes remain saved.")
        return 0
