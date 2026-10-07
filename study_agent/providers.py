"""Request options for the supported Chat Completions endpoints."""

from urllib.parse import urlsplit


def chat_options(base_url: str) -> dict:
    if urlsplit(base_url).hostname == "api.deepseek.com":
        # DeepSeek uses max_tokens; forced tool choice needs non-thinking mode.
        return {"max_tokens": 2400, "extra_body": {"thinking": {"type": "disabled"}}}
    return {"max_completion_tokens": 2400, "parallel_tool_calls": False}
