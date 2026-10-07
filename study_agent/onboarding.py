"""Interactive provider setup and personal notes management."""

import os
import re
import warnings
from getpass import GetPassWarning, getpass
from importlib.resources import files
from pathlib import Path
from uuid import uuid4

from openai import OpenAI

from .config import Settings
from .preferences import PRESETS, save_settings, validate_base_url


def configure(console, root: Path) -> Settings:
    console.print("\nConfigure StudyTrail | bring your own API")
    console.print("1. OpenAI-compatible custom endpoint  2. OpenAI  3. Groq")
    selection = console.input("Provider [1]: ").strip() or "1"
    providers = {"1": "custom", "2": "openai", "3": "groq"}
    if selection not in providers:
        raise ValueError("Choose 1, 2, or 3.")
    provider = providers[selection]
    base_url = PRESETS.get(provider)
    if base_url is None:
        base_url = console.input("API base URL (including /v1 if required): ").strip()
    base_url = validate_base_url(base_url)
    console.print(f"Your key and study requests will be sent to: {base_url}")
    console.print("Use a model supporting Chat Completions function/tool calling.")
    model = console.input("Model ID from your provider: ").strip()
    env_key = os.getenv("STUDYTRAIL_API_KEY", "").strip()
    key = env_key
    if not key:
        with warnings.catch_warnings():
            warnings.simplefilter("error", GetPassWarning)
            try:
                key = getpass("Paste API key (hidden): ").strip()
            except GetPassWarning as exc:
                raise RuntimeError(
                    "Hidden input is unavailable. Run config in an interactive terminal "
                    "or set STUDYTRAIL_API_KEY in your environment."
                ) from exc
    settings = Settings(root=root, provider=provider, base_url=base_url, model=model, api_key=key)
    settings.require_api()
    console.print("An optional connection test uses API quota and may incur provider charges.")
    if console.input("Test tool calling now? [y/N]: ").strip().lower() in {"y", "yes"}:
        probe_provider(settings)
        console.print("Tool-calling test passed.")
    else:
        console.print("Connection not verified. Your first chat will use the live API.")
    save_settings(settings, persist_key=not bool(env_key))
    console.print("Settings saved. API costs and limits depend on your provider and plan.")
    return settings


def probe_provider(settings: Settings) -> None:
    with OpenAI(
        api_key=settings.api_key, base_url=settings.base_url, timeout=30, max_retries=0
    ) as client:
        result = client.chat.completions.create(
            model=settings.model,
            messages=[{"role": "user", "content": "Call connection_check with no arguments."}],
            tools=[
                {
                    "type": "function",
                    "function": {
                        "name": "connection_check",
                        "description": "Check tool support without side effects.",
                        "parameters": {
                            "type": "object",
                            "properties": {},
                            "additionalProperties": False,
                        },
                    },
                }
            ],
            tool_choice={"type": "function", "function": {"name": "connection_check"}},
            parallel_tool_calls=False,
            max_completion_tokens=2400,
        )
        if not result.choices or not any(
            call.function.name == "connection_check"
            for call in (result.choices[0].message.tool_calls or [])
        ):
            raise ValueError("The model did not return the test tool call. Check compatibility.")


def subject_slug(value: str) -> str:
    value = value.strip().casefold()
    if not re.fullmatch(r"[a-z0-9][a-z0-9 -]{0,49}", value):
        raise ValueError(
            "Subject must be 1-50 letters/numbers/spaces/hyphens, e.g. java or history."
        )
    return re.sub(r"[ -]+", "-", value).rstrip("-")


def ensure_notes(root: Path) -> None:
    directory = root / "notes"
    directory.mkdir(parents=True, exist_ok=True)
    bundled = files("study_agent").joinpath("default_notes")
    for subject in ("python", "java"):
        for source in bundled.joinpath(subject).iterdir():
            target = directory / subject / source.name
            if not target.resolve().is_relative_to(directory.resolve()):
                raise ValueError("Bundled notes must stay inside the notes folder.")
            if not target.exists():
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(source.read_text(encoding="utf-8"), encoding="utf-8")


def save_note(root: Path, subject: str, title: str, content: str) -> Path:
    subject = subject_slug(subject)
    title = subject_slug(title)
    if not content.strip() or len(content.encode("utf-8")) > 200_000:
        raise ValueError("Notes must contain text and be at most 200 KB in UTF-8.")
    directory = root / "notes" / "personal" / subject
    if not directory.resolve().is_relative_to((root / "notes").resolve()):
        raise ValueError("Personal notes must stay inside the notes folder.")
    directory.mkdir(parents=True, exist_ok=True)
    target = directory / f"{title}-{uuid4().hex[:8]}.md"
    with target.open("x", encoding="utf-8") as stream:
        stream.write(content)
    return target


def manage_notes(console, root: Path) -> None:
    ensure_notes(root)
    console.print(f"\nNotes folder: {root / 'notes'}")
    console.print("1. Paste notes  2. Import .txt/.md  3. List subjects  0. Back")
    choice = console.input("Choose: ").strip()
    if choice == "0":
        return
    if choice == "3":
        subjects = {
            p.name
            for parent in (root / "notes", root / "notes/personal")
            if parent.exists()
            for p in parent.iterdir()
            if p.is_dir() and p.name not in {"personal", "private"}
        }
        console.print("Subjects: " + ", ".join(sorted(subjects)))
        return
    if choice not in {"1", "2"}:
        raise ValueError("Choose 0, 1, 2, or 3.")
    subject = subject_slug(console.input("Subject (e.g. java): "))
    title = subject_slug(console.input("Short note title: "))
    if choice == "2":
        path = Path(console.input("File path: ").strip().strip('"')).expanduser()
        if path.suffix.casefold() not in {".md", ".txt"}:
            raise ValueError("Import a UTF-8 .md or .txt file.")
        if path.stat().st_size > 200_000:
            raise ValueError("Files must be at most 200 KB.")
        content = path.read_text(encoding="utf-8")
    else:
        console.print("Paste your notes. Finish with .done on a line by itself.")
        lines = []
        size = 0
        while (line := console.input("")) != ".done":
            size += len(line.encode("utf-8")) + 1
            if size > 200_000:
                raise ValueError("Notes must be at most 200 KB.")
            lines.append(line)
        content = "\n".join(lines)
    path = save_note(root, subject, title, content)
    console.print(f"Saved: {path}")
    console.print("Matching passages may be sent to your AI provider during chat.")
