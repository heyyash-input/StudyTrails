import sys
from io import StringIO

import httpx
from openai import NotFoundError
from rich.console import Console

from study_agent import cli
from study_agent.config import Settings
from study_agent.storage import Store


def test_missing_model_error_explains_how_to_fix_configuration():
    response = httpx.Response(
        404,
        request=httpx.Request("POST", "https://api.groq.com/openai/v1/chat/completions"),
        headers={"x-request-id": "test-request-id"},
    )
    error = NotFoundError(
        "Model unavailable",
        response=response,
        body={"code": "model_not_found", "message": "Model unavailable"},
    )
    message = cli.describe_error(error)
    assert "studytrails config" in message
    assert "restart" in message
    assert "test-request-id" in message


def setup_cli(monkeypatch, tmp_path, command, answers=""):
    output = StringIO()
    monkeypatch.setattr(cli, "console", Console(file=output, force_terminal=False))
    monkeypatch.setattr(sys, "stdin", StringIO(answers))
    monkeypatch.setattr(sys, "argv", ["study_agent", *command])
    monkeypatch.setattr(Settings, "load", classmethod(lambda cls: Settings(root=tmp_path)))
    return output


def test_demo_runs_without_key_and_saves_only_demo_results(monkeypatch, tmp_path):
    notes = tmp_path / "notes"
    notes.mkdir()
    (notes / "loops.md").write_text("Python loops and range", encoding="utf-8")
    output = setup_cli(monkeypatch, tmp_path, ["demo"], "invalid\nb\nc\nd\n")
    assert cli.main() == 0
    assert "100.0%" in output.getvalue()
    assert "OFFLINE DEMO" in output.getvalue()
    assert (tmp_path / "data/demo.sqlite3").exists()
    assert not (tmp_path / "data/study.sqlite3").exists()


def test_quit_does_not_save_partial_attempt(monkeypatch, tmp_path, store, quiz):
    quiz_id = store.create_quiz(quiz)
    setup_cli(monkeypatch, tmp_path, ["demo"], "b\nq\n")
    cli.take_quiz(store, quiz_id)
    assert store.get_scores()["completed_quizzes"] == 0


def test_live_command_without_key_fails_before_creating_database(monkeypatch, tmp_path):
    output = setup_cli(monkeypatch, tmp_path, ["chat"])
    assert cli.main() == 1
    assert "GROQ_API_KEY" in output.getvalue()
    assert not (tmp_path / "data").exists()


def test_doctor_does_not_print_secret(monkeypatch, tmp_path):
    output = setup_cli(monkeypatch, tmp_path, ["doctor"])
    monkeypatch.setattr(
        Settings,
        "load",
        classmethod(lambda cls: Settings(root=tmp_path, api_key="secret-test-value")),
    )
    assert cli.main() == 0
    assert "configured (not verified)" in output.getvalue()
    assert "secret-test-value" not in output.getvalue()


def test_demo_resume_instructions_use_demo_database(monkeypatch, tmp_path, quiz):
    store = Store(tmp_path / "demo.sqlite3")
    quiz_id = store.create_quiz(quiz)
    output = setup_cli(monkeypatch, tmp_path, ["demo"], "q\n")
    cli.take_quiz(store, quiz_id)
    assert f"{quiz_id} --demo" in " ".join(output.getvalue().split())
    cli.show_pending(store)
    assert "QUIZ_ID --demo" in " ".join(output.getvalue().split())
