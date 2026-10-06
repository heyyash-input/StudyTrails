"""Load settings without exposing secrets or requiring a key for offline commands."""

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent


@dataclass(frozen=True)
class Settings:
    root: Path = PROJECT_ROOT
    model: str = "openai/gpt-oss-120b"
    api_key: str = ""

    @classmethod
    def load(cls) -> "Settings":
        load_dotenv(PROJECT_ROOT / ".env", override=False)
        return cls(
            model=os.getenv("GROQ_MODEL", "openai/gpt-oss-120b").strip(),
            api_key=os.getenv("GROQ_API_KEY", "").strip(),
        )

    def require_api(self) -> None:
        if not self.api_key or self.api_key.lower().startswith(("your-", "replace")):
            raise ValueError(
                "Set GROQ_API_KEY in the project's .env file first. "
                "You can run 'uv run python -m study_agent demo' without a key."
            )
        if not self.model:
            raise ValueError("GROQ_MODEL must contain a model name.")
