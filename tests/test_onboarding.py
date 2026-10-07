import json
from io import StringIO
from types import SimpleNamespace

import httpx
import pytest
from keyring.errors import KeyringError
from openai import OpenAI
from rich.console import Console

from study_agent import cli, onboarding, preferences
from study_agent.config import Settings
from study_agent.notes import search_notes
from study_agent.tools import StudyTools


@pytest.fixture(autouse=True)
def isolated_settings(monkeypatch, tmp_path):
    monkeypatch.setenv("STUDYTRAIL_HOME", str(tmp_path))
    for name in (
        "STUDYTRAIL_API_KEY",
        "STUDYTRAIL_BASE_URL",
        "STUDYTRAIL_MODEL",
        "GROQ_API_KEY",
        "GROQ_MODEL",
    ):
        monkeypatch.delenv(name, raising=False)


@pytest.fixture
def vault(monkeypatch):
    values = {}
    fake = SimpleNamespace(
        set_password=lambda service, name, value: values.update({(service, name): value}),
        get_password=lambda service, name: values.get((service, name)),
    )
    monkeypatch.setattr(preferences, "secure_backend", lambda: fake)
    return values


def test_provider_switch_never_reuses_another_providers_key(tmp_path, vault):
    one = Settings(
        root=tmp_path,
        provider="custom",
        model="model-a",
        api_key="secret-a",
        base_url="https://one.example/v1",
    )
    preferences.save_settings(one)
    assert Settings.load().api_key == "secret-a"
    two = Settings(
        root=tmp_path,
        provider="custom",
        model="model-b",
        api_key="secret-b",
        base_url="https://two.example/v1",
    )
    preferences.save_settings(two)
    loaded = Settings.load()
    assert loaded.base_url == two.base_url
    assert loaded.api_key == "secret-b"
    assert "secret" not in (tmp_path / "config.json").read_text()
    assert "secret" not in repr(loaded)
    assert len(vault) == 2


def test_no_keyring_fails_without_plaintext_fallback(tmp_path, monkeypatch):
    def unavailable():
        raise KeyringError("unavailable")

    monkeypatch.setattr(preferences, "secure_backend", unavailable)
    with pytest.raises(RuntimeError, match="No usable secure credential store"):
        preferences.save_settings(Settings(root=tmp_path, api_key="test-key"))
    assert not (tmp_path / "config.json").exists()
    preferences.save_settings(Settings(root=tmp_path, api_key="test-key"), persist_key=False)
    assert Settings.load().api_key == ""
    monkeypatch.setenv("STUDYTRAIL_API_KEY", "environment-key")
    assert Settings.load().api_key == "environment-key"


@pytest.mark.parametrize(
    "url",
    [
        "http://remote.example/v1",
        "https://user:secret@api.example/v1",
        "https://api.example/v1?key=secret",
        "file:///tmp/key",
    ],
)
def test_unsafe_endpoint_is_rejected(url):
    with pytest.raises(ValueError):
        preferences.validate_base_url(url)


def test_local_endpoint_is_allowed():
    assert preferences.validate_base_url("http://localhost:11434/v1/") == (
        "http://localhost:11434/v1"
    )


def test_setup_saves_only_settings_and_masks_key(tmp_path, monkeypatch, vault):
    output = StringIO()
    console = Console(file=output)
    answers = iter(["1", "https://example.test/v1", "tool-model", "n"])
    monkeypatch.setattr(console, "input", lambda *args: next(answers))
    monkeypatch.setattr(onboarding, "getpass", lambda *args: "hidden-test-secret")
    settings = onboarding.configure(console, tmp_path)
    assert settings.model == "tool-model"
    assert Settings.load().api_key == "hidden-test-secret"
    assert "hidden-test-secret" not in output.getvalue()
    assert "not verified" in output.getvalue()


def test_failed_probe_does_not_replace_config(tmp_path, monkeypatch, vault):
    original = Settings(root=tmp_path, api_key="old-key")
    preferences.save_settings(original)
    before = (tmp_path / "config.json").read_bytes()
    console = Console(file=StringIO())
    answers = iter(["2", "new-model", "y"])
    monkeypatch.setattr(console, "input", lambda *args: next(answers))
    monkeypatch.setattr(onboarding, "getpass", lambda *args: "new-key")

    def fail(settings):
        raise ValueError("Unsupported tool calling")

    monkeypatch.setattr(onboarding, "probe_provider", fail)
    with pytest.raises(ValueError, match="Unsupported"):
        onboarding.configure(console, tmp_path)
    assert (tmp_path / "config.json").read_bytes() == before
    assert Settings.load().api_key == "old-key"


@pytest.mark.parametrize("supported", [True, False])
@pytest.mark.parametrize("base_url", ["https://provider.example/v1", "https://api.deepseek.com"])
def test_connection_probe_checks_actual_tool_response(tmp_path, monkeypatch, supported, base_url):
    def handler(request):
        assert str(request.url) == base_url + "/chat/completions"
        payload = json.loads(request.content)
        if base_url == "https://api.deepseek.com":
            assert payload["thinking"] == {"type": "disabled"}
            assert payload["max_tokens"] == 2400
            assert "max_completion_tokens" not in payload
            assert "parallel_tool_calls" not in payload
        assert payload["tool_choice"]["function"]["name"] == "connection_check"
        assert payload["model"] == "tool-model"
        message = {"role": "assistant", "content": "Hello"}
        if supported:
            message["tool_calls"] = [
                {
                    "id": "check1",
                    "type": "function",
                    "function": {"name": "connection_check", "arguments": "{}"},
                }
            ]
        return httpx.Response(
            200,
            json={
                "id": "probe",
                "object": "chat.completion",
                "created": 0,
                "model": "tool-model",
                "choices": [
                    {
                        "index": 0,
                        "message": message,
                        "finish_reason": "tool_calls" if supported else "stop",
                    }
                ],
            },
        )

    with httpx.Client(transport=httpx.MockTransport(handler)) as http:
        monkeypatch.setattr(
            onboarding, "OpenAI", lambda **kwargs: OpenAI(http_client=http, **kwargs)
        )
        settings = Settings(
            root=tmp_path,
            base_url=base_url,
            model="tool-model",
            api_key="fake-key",
        )
        if supported:
            onboarding.probe_provider(settings)
        else:
            with pytest.raises(ValueError, match="test tool call"):
                onboarding.probe_provider(settings)


def test_subject_notes_are_isolated_and_additions_do_not_overwrite(tmp_path):
    onboarding.ensure_notes(tmp_path)
    one = onboarding.save_note(tmp_path, "Java", "Loops", "Java loops repeat statements.")
    two = onboarding.save_note(tmp_path, "Java", "Loops", "Java loops can use break.")
    onboarding.save_note(tmp_path, "Python", "Loops", "Python loops use range.")
    assert one != two and one.exists() and two.exists()
    passages = search_notes(tmp_path / "notes", "loops", "java")
    assert any("Java loops" in passage["text"] for passage in passages)
    assert all("python" not in passage["source"] for passage in passages)
    assert all(passage["line"] >= 1 for passage in passages)
    with pytest.raises(ValueError):
        onboarding.save_note(tmp_path, "../outside", "Title", "No escape")
    with pytest.raises(ValueError):
        onboarding.save_note(tmp_path, "java", "Title", "x" * 200_001)


def test_subject_is_recorded_in_quiz_topic(store, tmp_path, quiz):
    tools = StudyTools(store, tmp_path, subject="java")
    result = tools.execute("create_quiz", quiz.model_dump_json())
    assert store.get_quiz(result["quiz_id"]).topic.startswith("java ")


def test_menu_offline_first_run_exits_without_network(tmp_path, monkeypatch):
    output = StringIO()
    console = Console(file=output)
    answers = iter(["n", "0"])
    monkeypatch.setattr(console, "input", lambda *args: next(answers))
    monkeypatch.setattr(cli, "console", console)
    cli.menu(Settings(root=tmp_path))
    assert "Welcome to StudyTrail" in output.getvalue()
    assert not (tmp_path / "config.json").exists()
    assert not (tmp_path / "data").exists()


def test_bundled_notes_are_not_overwritten(tmp_path):
    onboarding.ensure_notes(tmp_path)
    path = tmp_path / "notes/python/loops.md"
    path.write_text("My edited loops notes", encoding="utf-8")
    onboarding.ensure_notes(tmp_path)
    assert path.read_text() == "My edited loops notes"


def test_corrupt_preferences_produce_clear_error(tmp_path):
    (tmp_path / "config.json").write_text(json.dumps({"model": 2}))
    with pytest.raises(ValueError, match="config.json"):
        Settings.load()


def test_custom_environment_does_not_use_legacy_key(monkeypatch):
    monkeypatch.setenv("STUDYTRAIL_BASE_URL", "https://other.example/v1")
    monkeypatch.setenv("STUDYTRAIL_MODEL", "custom-model")
    monkeypatch.setenv("GROQ_API_KEY", "legacy-secret")
    settings = Settings.load()
    assert settings.api_key == ""
    assert settings.model == "custom-model"


def test_installed_storage_uses_personal_directory(tmp_path, monkeypatch):
    monkeypatch.delenv("STUDYTRAIL_HOME")
    monkeypatch.setattr(preferences, "PROJECT_ROOT", tmp_path / "site-packages")
    monkeypatch.setattr(
        preferences, "user_data_path", lambda *args, **kwargs: tmp_path / "personal"
    )
    assert preferences.data_root() == tmp_path / "personal"


def test_existing_checkout_keeps_its_storage(tmp_path, monkeypatch):
    monkeypatch.delenv("STUDYTRAIL_HOME")
    (tmp_path / "pyproject.toml").write_text("[project]\nname='studytrails'\n")
    (tmp_path / "data").mkdir()
    database = tmp_path / "data/study.sqlite3"
    database.write_bytes(b"existing progress is not rewritten")
    monkeypatch.setattr(preferences, "PROJECT_ROOT", tmp_path)
    assert preferences.data_root() == tmp_path
    onboarding.ensure_notes(tmp_path)
    assert database.read_bytes() == b"existing progress is not rewritten"


def test_import_notes_and_reject_pdf(tmp_path, monkeypatch):
    source = tmp_path / "source.txt"
    source.write_text("Inheritance lets a class extend another class.", encoding="utf-8")
    console = Console(file=StringIO())
    answers = iter(["2", "java", "inheritance", str(source)])
    monkeypatch.setattr(console, "input", lambda *args: next(answers))
    onboarding.manage_notes(console, tmp_path)
    assert search_notes(tmp_path / "notes", "inheritance", "java")
    answers = iter(["2", "java", "book", "book.pdf"])
    with pytest.raises(ValueError, match="UTF-8"):
        onboarding.manage_notes(console, tmp_path)


def test_deepseek_setup_default_model_and_literal_prompts(tmp_path, monkeypatch, vault):
    import sys

    output = StringIO()
    console = Console(file=output, width=100)
    monkeypatch.setattr(sys, "stdin", StringIO("4\n\nmaybe\nn\n"))
    monkeypatch.setattr(onboarding, "getpass", lambda *args: "deepseek-test-secret")
    settings = onboarding.configure(console, tmp_path)
    loaded = Settings.load()
    assert loaded.provider == settings.provider == "deepseek"
    assert loaded.base_url == "https://api.deepseek.com"
    assert loaded.model == "deepseek-flash"
    assert loaded.api_key == "deepseek-test-secret"
    assert "deepseek-test-secret" not in output.getvalue()
    assert "deepseek-test-secret" not in (tmp_path / "config.json").read_text()
    assert "Provider [1]:" in output.getvalue()
    assert "Model ID [deepseek-flash]:" in output.getvalue()
    assert "[y/n] (Enter = no):" in output.getvalue()
    assert "Please enter y for yes or n for no." in output.getvalue()
