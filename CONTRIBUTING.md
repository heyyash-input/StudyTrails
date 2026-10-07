# Contributing to StudyTrail

Thanks for helping make StudyTrail easier to learn from and more useful to study with.
Small, focused improvements are welcome, including documentation-only changes.

## Choose a contribution

- Report a bug with clear steps to reproduce it.
- Improve setup instructions or add a useful example.
- Add accurate study notes you wrote or have permission to share.
- Fix a proven issue and add a regression test when appropriate.
- Discuss a larger feature before starting substantial implementation.

Current areas to explore include retrieval evaluation, more provider integrations,
and terminal usability. Discuss changes before expanding the supported API formats.

## Set up locally

Fork the repository on its hosting service, then clone your fork under
`C:\CLAUDE_env`. If you received a source download, you can still develop locally
and share a focused patch with the maintainer.

From the project folder in PowerShell:

```powershell
uv sync --locked
uv run python -m study_agent demo
```

Use the project's `.venv`; do not install dependencies into system Python.
The demo and automated tests do not need an API key. Live checks use your selected provider account and its limits. Keep real keys in
the OS credential store or environment, never in test fixtures or committed files.

## Make a focused change

1. Create a descriptive branch, for example `fix/quiz-resume-message`.
2. Reproduce a bug before fixing it, or describe the intended new behaviour.
3. Make the smallest useful change; avoid unrelated refactoring.
4. Add meaningful tests for changed behaviour. Documentation-only changes do not
   need new application tests.
5. Update the README or user guide when commands or behaviour change.

```powershell
uv run git switch -c fix/quiz-resume-message
uv run ruff format .
uv run ruff check .
uv run ruff format --check .
uv run pytest -q
```

Tests use temporary databases and mocked model responses. They must not make live
API calls, depend on personal credentials, or modify real study progress.
If dependencies change, update both `pyproject.toml` and `uv.lock` using uv.

## Open a pull request

Explain:

- The problem or user need.
- What changes for the user, with a small example where helpful.
- How you checked the change.
- Any known limitations or follow-up work.

For terminal changes, a short before/after transcript is helpful. For visuals,
include a preview. Keep screenshots and logs free of keys and private notes.

Before committing, review what will be shared:

```powershell
uv run git status --short
uv run git diff
```

Stage only the intended files. Do not commit `.env`, `.venv`, `data/`, private notes,
or local caches. `.env.example` should contain names and placeholders only.

## Report an issue

Include the command or prompt you used, expected behaviour, actual behaviour, and
steps another person can repeat. For API problems, include the model name, HTTP
status, and request ID when available. Never include the API key.

If reporting an incorrect quiz answer, share the question, options, explanation,
and why you believe it is wrong. AI-generated content is not guaranteed correct.

## Review expectations

Be clear, constructive, and respectful. Prefer evidence over assumptions and simple
code over unnecessary abstraction. Contributions are reviewed; submitting one does
not guarantee it will be merged.

StudyTrail uses the MIT licence. Contributions are provided under the same terms;
see [LICENSE](LICENSE).

[Back to StudyTrail](README.md)
