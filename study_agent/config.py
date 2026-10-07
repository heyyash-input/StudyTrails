"""Load settings without exposing secrets or requiring a key for offline commands."""

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

from .preferences import PRESETS, data_root, read_preferences, validate_base_url


@dataclass(frozen=True)
class Settings:
    root: Path = field(default_factory=data_root)
    model: str = "openai/gpt-oss-120b"
    api_key: str = field(default="", repr=False)
    provider: str = "groq"
    base_url: str = PRESETS["groq"]

    @classmethod
    def load(cls) -> "Settings":
        root = data_root()
        saved = read_preferences(root)
        if saved is not None:
            return cls(root=root, **saved)
        if (root / "pyproject.toml").is_file():
            load_dotenv(root / ".env", override=False)
        if base_url := os.getenv("STUDYTRAIL_BASE_URL", "").strip():
            return cls(
                root=root,
                provider="custom",
                base_url=validate_base_url(base_url),
                model=os.getenv("STUDYTRAIL_MODEL", "").strip(),
                api_key=os.getenv("STUDYTRAIL_API_KEY", "").strip(),
            )
        if not os.getenv("GROQ_API_KEY") and not os.getenv("GROQ_MODEL"):
            return cls(root=root, provider="not configured", model="", base_url="")
        return cls(
            root=root,
            model=os.getenv("GROQ_MODEL", "openai/gpt-oss-120b").strip(),
            api_key=os.getenv("GROQ_API_KEY", "").strip(),
        )

    def require_api(self) -> None:
        if not self.api_key or self.api_key.lower().startswith(("your-", "replace")):
            raise ValueError(
                "Run 'studytrails config' to configure your API key. "
                "Legacy GROQ_API_KEY is supported. "
                "Run 'studytrails demo' without a key."
            )
        if not self.model:
            raise ValueError("Configure a model with 'studytrails config'.")

        validate_base_url(self.base_url)
