import pytest

from study_agent import config


def test_groq_configuration_uses_its_own_key_and_model(monkeypatch):
    monkeypatch.setattr(config, "load_dotenv", lambda *args, **kwargs: None)
    monkeypatch.setenv("GROQ_API_KEY", "test-groq-key")
    monkeypatch.setenv("GROQ_MODEL", "openai/gpt-oss-120b")
    monkeypatch.setenv("OPENAI_API_KEY", "test-other-provider-key")
    monkeypatch.setenv("OPENAI_MODEL", "test-other-provider-model")
    settings = config.Settings.load()
    assert settings.api_key == "test-groq-key"
    assert settings.model == "openai/gpt-oss-120b"


def test_missing_groq_key_does_not_fall_back_to_openai(monkeypatch):
    monkeypatch.setattr(config, "load_dotenv", lambda *args, **kwargs: None)
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    monkeypatch.delenv("GROQ_MODEL", raising=False)
    monkeypatch.setenv("OPENAI_API_KEY", "test-other-provider-key")
    settings = config.Settings.load()
    assert settings.model == "openai/gpt-oss-120b"
    with pytest.raises(ValueError, match="GROQ_API_KEY"):
        settings.require_api()
