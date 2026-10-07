"""Terminal entry point. User answers, not model claims, drive saved results."""

import argparse
import sqlite3

from openai import APIConnectionError, APIError, APIStatusError, AuthenticationError, RateLimitError
from rich.console import Console

from .agent import StudyAgent
from .config import Settings
from .demo import prepare_demo
from .notes import search_notes
from .onboarding import configure, ensure_notes, manage_notes, subject_slug
from .preferences import data_root
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
                console.print(f"Nothing submitted. Resume with: studytrails quiz {quiz_id}{mode}")
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
            console.print(f"Saved for later: studytrails quiz {quiz_id}")


def describe_error(exc: Exception) -> str:
    # Do not print raw provider responses, request headers, or API keys.
    if isinstance(exc, AuthenticationError):
        return "API authentication failed. Run 'studytrails config' to check your key and provider."
    if isinstance(exc, RateLimitError):
        return (
            "API quota or rate limit reached. Wait for your provider limit "
            "to reset or check your provider account."
        )
    if isinstance(exc, APIConnectionError):
        return "Could not reach the API. Check your network, then try again."
    if isinstance(exc, APIStatusError):
        if exc.status_code == 404 and exc.code == "model_not_found":
            return (
                "The provider cannot access the configured model. Run 'studytrails config' "
                "to select an available model, then restart the app. "
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
    console.print("Try: Explain a topic from my notes and give me 3 practice questions.")
    console.print(
        "Commands: /scores, /pending, /quit. "
        "Each request uses your provider API quota and may incur charges."
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
        console.print(f"Take one with: studytrails quiz QUIZ_ID{mode}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="StudyTrail: your personal multi-subject AI study coach."
    )
    commands = parser.add_subparsers(dest="command")
    commands.add_parser("demo", help="Try a fixed offline quiz; no API key or network required.")
    live = commands.add_parser("chat", help="Start the live tool-using AI coach.")
    live.add_argument("--subject", type=subject_slug)
    ask = commands.add_parser("ask", help="Send one study request to the live AI coach.")
    ask.add_argument("goal")
    ask.add_argument("--subject", type=subject_slug)
    commands.add_parser("config", help="Configure your provider, model, and API key.")
    commands.add_parser("notes-add", help="Paste or import notes by subject.")
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
    notes.add_argument("--subject", type=subject_slug)
    return parser


def menu(settings: Settings) -> None:
    console.print("\nWelcome to StudyTrail!", style="bold cyan")
    console.print("Learn from your notes. Practise with quizzes. Track your progress.")
    ensure_notes(settings.root)
    if not settings.api_key:
        console.print("No API key configured. Offline notes, scores, and demo remain available.")
        if console.input("Configure AI now? [y/N]: ").strip().lower() in {"y", "yes"}:
            settings = configure(console, settings.root)
    while True:
        console.print("\n1. Start learning  2. Manage notes  3. View progress")
        console.print("4. Configure AI  5. Pending quizzes  6. Offline demo  0. Exit")
        choice = console.input("Choose: ").strip()
        if choice == "0":
            return
        try:
            if choice == "4":
                settings = configure(console, settings.root)
            elif choice == "2":
                manage_notes(console, settings.root)
            elif choice in {"1", "3", "5", "6"}:
                subject = None
                if choice == "1":
                    settings.require_api()
                    value = console.input("Subject (e.g. java; blank for all subjects): ").strip()
                    subject = subject_slug(value) if value else None
                db = "demo.sqlite3" if choice == "6" else "study.sqlite3"
                store = Store(settings.root / "data" / db)
                tools = StudyTools(store, settings.root / "notes", subject)
                if choice == "1":
                    chat(settings, tools)
                elif choice == "3":
                    show_scores(store)
                elif choice == "5":
                    show_pending(store)
                    quiz_id = console.input("Quiz ID to take (blank to return): ").strip()
                    if quiz_id:
                        take_quiz(store, quiz_id)
                else:
                    console.print("OFFLINE DEMO: fixed Python questions, separate scores.")
                    take_quiz(store, prepare_demo(tools, trace))
            else:
                console.print("Choose a number from 0 to 6.")
        except (ValueError, RuntimeError, APIError, OSError, sqlite3.Error) as exc:
            console.print(f"Error: {describe_error(exc)}", style="red")


def main() -> int:
    args = build_parser().parse_args()
    try:
        if args.command == "config":
            configure(console, data_root())
            return 0
        settings = Settings.load()
        if args.command is None:
            menu(settings)
            return 0
        if args.command == "notes-add":
            manage_notes(console, settings.root)
            return 0
        if args.command == "doctor":
            console.print(f"Storage: {settings.root}")
            console.print(f"Provider: {settings.provider}")
            console.print(f"API endpoint: {settings.base_url or '(not configured)'}")
            console.print(f"Model: {settings.model or '(missing)'}")
            console.print(
                f"API key: {'configured (not verified)' if settings.api_key else 'not configured'}"
            )
            console.print(f"Notes: {settings.root / 'notes'}")
            console.print("Offline demo is available. This check does not contact the API.")
            return 0
        if args.command == "notes":
            ensure_notes(settings.root)
            passages = search_notes(settings.root / "notes", args.query, args.subject)
            for passage in passages:
                console.print(f"\n[{passage['source']}:{passage['line']}]\n{passage['text']}")
            if not passages:
                console.print("No matching notes. Try a specific topic such as loops or functions.")
            return 0
        if args.command in {"chat", "ask"}:
            settings.require_api()
        ensure_notes(settings.root)
        demo_mode = args.command == "demo" or getattr(args, "demo", False)
        db_name = "demo.sqlite3" if demo_mode else "study.sqlite3"
        store = Store(settings.root / "data" / db_name)
        tools = StudyTools(store, settings.root / "notes", getattr(args, "subject", None))
        if demo_mode:
            console.print(
                "OFFLINE DEMO — fixed content, no AI calls; demo scores are separate.",
                style="yellow",
            )
        match args.command:
            case "demo":
                quiz_id = prepare_demo(tools, trace)
                take_quiz(store, quiz_id)
                console.print("\nNext: run studytrails config, then studytrails chat")
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
