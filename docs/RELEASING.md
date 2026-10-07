# Releasing StudyTrail

The distribution name is `studytrails`; the import remains `study_agent`.
Version 0.2.0 is published on PyPI. Version 0.2.1 is the next local candidate.
Build, tests, and CI do not publish a release.

## Before each release

1. Choose a new version in `pyproject.toml`. PyPI versions cannot be overwritten;
   check that the version has not already been published.
2. Review the MIT licence and package metadata. Add your public repository URL to
   `[project.urls]` when ready; no repository URL is invented by this project.
3. Check package contents for accidental secrets, databases, or personal notes.
   Wheels include only the `study_agent` package and its bundled example notes.
   Source distributions use an explicit allowlist. `notes/`, `.env`, and `data/`
   from the local checkout are not published.
4. Commit and push the reviewed source to GitHub. Use absolute public links/images
   in the PyPI description if adding repository branding there. The package uses a
   self-contained `docs/PYPI.md` description.

## Build and verify

From the project under `C:\CLAUDE_env`:

```powershell
uv sync --locked
uv run ruff check .
uv run ruff format --check .
uv run pytest -q
uv build
```

If the local sandbox blocks pytest's temporary folder, supply `--basetemp` with a
new, dedicated writable test directory. Do not point it at existing valuable data:
pytest manages that directory itself.

Install the wheel in a separate uv-managed environment and test outside the source
checkout. The CI workflow also builds and installs the wheel. Verify the welcome
menu, offline demo, note search, and configuration recovery with temporary storage.
Test real provider access only with your own credentials and awareness of quota.
The automated suite mocks providers and the OS vault; it does not certify every
provider/model or every desktop keyring configuration.

## Publish when approved

Prefer PyPI Trusted Publishing with a reviewed GitHub release workflow, or use a
scoped upload token held in your local environment. Never commit upload tokens.
TestPyPI is a separate service with separate accounts, tokens, and project names.
Install dependencies from the regular index when testing a TestPyPI package; avoid
blindly combining indexes for production installs.

For a manual release, first review the files listed under `dist/`, then publish:

```powershell
uv publish
```

Supply authentication securely as documented by uv. This command publishes publicly;
it is not part of the build/test workflow. A published version cannot be replaced
with different contents; increment the version for a correction.

After publishing, confirm the new version on PyPI and install it in a fresh
environment. Users can update with `python -m pip install --upgrade studytrails`
or `uv tool upgrade studytrails`.

References: [uv publishing](https://docs.astral.sh/uv/guides/package/),
[PyPI Trusted Publishing](https://docs.pypi.org/trusted-publishers/), and
[Python packaging](https://packaging.python.org/en/latest/tutorials/packaging-projects/).
