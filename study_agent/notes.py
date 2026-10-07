"""Small, transparent keyword retrieval over local Markdown and text notes."""

import re
from pathlib import Path


def search_notes(directory: Path, query: str, subject: str | None = None) -> list[dict]:
    if not directory.is_dir():
        raise ValueError(f"Notes folder does not exist: {directory}")
    terms = set(re.findall(r"\w+", query.casefold()))
    terms -= {"a", "an", "the", "in", "of", "to", "my", "me", "help", "with"}
    if not terms:
        return []
    results = []
    root = directory.resolve()
    scopes = [directory / subject, directory / "personal" / subject] if subject else [directory]
    if any(not scope.resolve().is_relative_to(root) for scope in scopes):
        raise ValueError("Invalid subject folder.")
    for path in sorted({p for scope in scopes for p in scope.rglob("*")}):
        if path.suffix.lower() not in {".md", ".txt"} or not path.is_file():
            continue
        # Notes may contain links, but retrieval is confined to the notes directory.
        if not path.resolve().is_relative_to(root) or path.stat().st_size > 200_000:
            continue
        lines = path.read_text(encoding="utf-8").splitlines()
        for start in range(0, len(lines), 18):
            passage = "\n".join(lines[start : start + 24])[:2500]
            words = set(re.findall(r"\w+", passage.casefold()))
            score = len(terms & words)
            if score:
                results.append(
                    {
                        "source": path.relative_to(directory).as_posix(),
                        "line": start + 1,
                        "text": passage,
                        "score": score,
                    }
                )
    return sorted(results, key=lambda item: (-item["score"], item["source"], item["line"]))[:4]
