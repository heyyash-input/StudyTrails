"""Personal storage and credentials for installed users."""

import json
import os
from pathlib import Path
from urllib.parse import urlsplit

import keyring
from keyring.errors import KeyringError
from platformdirs import user_data_path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PRESETS = {
    "openai": "https://api.openai.com/v1",
    "groq": "https://api.groq.com/openai/v1",
    "deepseek": "https://api.deepseek.com",
}


def data_root() -> Path:
    if override := os.getenv("STUDYTRAIL_HOME"):
        return Path(override).expanduser().resolve()
    if (PROJECT_ROOT / "pyproject.toml").is_file():
        return PROJECT_ROOT
    return user_data_path("StudyTrail", appauthor=False)


def validate_base_url(value: str) -> str:
    url = urlsplit(value)
    local = url.hostname in {"localhost", "127.0.0.1", "::1"}
    if (
        not url.hostname
        or url.username
        or url.password
        or url.query
        or url.fragment
        or not (url.scheme == "https" or (url.scheme == "http" and local))
    ):
        raise ValueError("Use an HTTPS API base URL (HTTP is allowed only for localhost).")
    return value.rstrip("/")


def credential_service(root: Path, base_url: str) -> str:
    return f"StudyTrail:{root.resolve()}:{base_url}"


def secure_backend():
    """Use an OS credential store, never a plaintext fallback or arbitrary chain."""
    backend = keyring.get_keyring()
    candidates = getattr(backend, "backends", [backend])
    allowed = {
        "keyring.backends.Windows",
        "keyring.backends.macOS",
        "keyring.backends.SecretService",
        "keyring.backends.kwallet",
        "keyring.backends.libsecret",
    }
    for candidate in candidates:
        if type(candidate).__module__ in allowed:
            return candidate
    raise KeyringError("No supported operating-system credential store.")


def read_preferences(root: Path) -> dict | None:
    path = root / "config.json"
    if not path.exists():
        return None
    saved = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(saved, dict) or not all(
        isinstance(saved.get(k), str) for k in ("provider", "model", "base_url")
    ):
        raise ValueError("Invalid config.json. Run 'studytrails config' to replace it.")
    saved["base_url"] = validate_base_url(saved["base_url"])
    key = os.getenv("STUDYTRAIL_API_KEY", "").strip()
    if not key:
        try:
            key = (
                secure_backend().get_password(
                    credential_service(root, saved["base_url"]), "api_key"
                )
                or ""
            )
        except KeyringError:
            key = ""  # Offline commands remain usable without a credential backend.
    return {k: saved[k] for k in ("provider", "model", "base_url")} | {"api_key": key}


def save_settings(settings, persist_key: bool = True) -> None:
    settings.require_api()
    settings.root.mkdir(parents=True, exist_ok=True)
    if persist_key:
        try:
            secure_backend().set_password(
                credential_service(settings.root, settings.base_url), "api_key", settings.api_key
            )
        except KeyringError as exc:
            raise RuntimeError(
                "No usable secure credential store. Set STUDYTRAIL_API_KEY in your "
                "environment and run config again; no plaintext key was saved."
            ) from exc
    target = settings.root / "config.json"
    temp = target.with_suffix(".tmp")
    temp.write_text(
        json.dumps(
            {"provider": settings.provider, "base_url": settings.base_url, "model": settings.model},
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    temp.replace(target)
