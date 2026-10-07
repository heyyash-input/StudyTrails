<p align="center">
  <img src="assets/banner.svg" alt="StudyTrail - your personal AI study coach" width="100%">
</p>

# StudyTrail

**Learn a little. Practise with purpose. See your progress.**

StudyTrail is a terminal study coach for Python, Java, and other subjects. Bring
an API key from a compatible provider, add your notes, and practise with quizzes.
Your progress stays on your computer. You do not need to run a server.

StudyTrail was created by Yash Patil, a Python and AI learner. The project uses
OpenAI's Python SDK for compatible chat APIs. OpenAI created the GPT-OSS model
family; the API host may be another provider, such as Groq, and users can select
other model families too.

**Python 3.12 or 3.13 | Your choice of compatible AI provider | Local progress**

## Get started

Install the published release in a virtual environment (recommended for people new
to Python):

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install studytrails
studytrails
```

On macOS/Linux, use these commands instead:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install studytrails
studytrails
```

After activating `.venv`, users can run `studytrails` whenever they open a new
terminal for that environment. See the [downloadable setup guide](docs/SETUP.md)
for uv installation, first-run configuration, and troubleshooting.

For a one-time isolated CLI installation, `uv tool install studytrails` installs
the command so it can run from any directory without activating a virtual environment.

## First launch

```text
Welcome to StudyTrail!
Learn from your notes. Practise with quizzes. Track your progress.

Configure AI now? [y/N]:

1. Start learning  2. Manage notes  3. View progress
4. Configure AI  5. Pending quizzes  6. Offline demo  0. Exit
```

Choose **Configure AI** to supply:

1. An OpenAI-compatible custom endpoint, or the OpenAI/Groq address preset.
2. The exact model ID from your provider. It must support Chat Completions tool calling.
3. Your API key, entered with hidden input.

The app displays the destination before you enter your key. An API key is not
universal: it must match the endpoint and model. Native APIs with a different
protocol are not supported by this release. A preset supplies an address; it is
not a guarantee that every model at that provider is compatible.

You can optionally test tool calling during setup. This makes a small API request
and may consume paid quota. Skipping it saves unverified settings. Provider
compatibility is covered with mocked HTTP tests; no live cross-provider certification
is claimed.

Keys are saved using a supported operating-system credential store. They are never
written to `config.json`. If your machine has no usable credential store, supply
`STUDYTRAIL_API_KEY` through your environment and rerun setup. There is no plaintext
fallback. Run `studytrails config` to change providers or models later.

**Free app does not mean free API.** Offline features need no API calls. Live
coaching uses your provider's free allowance or paid plan. StudyTrail cannot inspect
or enforce your billing tier. One study request may make several API calls.

## Learn using your notes

Choose **Manage notes**, then paste text or import a UTF-8 `.txt` or `.md` file.
Give it a subject such as `java`, `python`, or `world-history`, and a short title.
When pasting, enter `.done` on its own line to finish.

Choose **Start learning** and enter the same subject. A blank subject searches all
notes. Try:

```text
Explain inheritance using my Java notes, then give me two beginner questions.
Review my scores and suggest what to practise next.
```

Notes are organised by subject. Search is restricted to the selected subject and
returns passages with filename/line references. New quiz topics include that
subject, so `java loops` and `python loops` have separate score labels. Historical
quiz labels are retained unchanged; scores display all topics.

No model training happens. This is keyword retrieval: good headings, concrete
terms, and clear examples help. PDF, Word, images, and embeddings are not supported.
Files above 200 KB are skipped. Matching passages are sent to the selected provider;
only add material you are comfortable sharing with that provider. AI answers,
answer keys, and citations still need your judgment.

## Practise and track progress

Choose A, B, C, or D during a quiz. StudyTrail grades and saves your submitted answers,
then displays explanations. Enter Q to leave without submitting. Resuming starts
from question one. A completed quiz cannot be submitted twice.

Inside chat, use `/scores`, `/pending`, or `/quit`. Chat history lasts for the current
session; completed results survive restarts. The offline demo uses fixed Python
questions and a separate database. It is not a local AI model.

## Useful commands

```powershell
studytrails
studytrails config
studytrails chat --subject java
studytrails ask "Explain Java inheritance" --subject java
studytrails notes-add
studytrails notes "inheritance" --subject java
studytrails scores
studytrails pending
studytrails quiz QUIZ_ID
studytrails demo
studytrails doctor
studytrails --help
```

Add `--demo` to `scores`, `pending`, or `quiz QUIZ_ID` to use demo progress.
`doctor` reports paths and settings without exposing the key or contacting the API.
All commands also work after `uv run python -m study_agent` in the source checkout.

## Where are my files?

Installed releases use your operating system's personal application-data directory
(for example `%LOCALAPPDATA%\StudyTrail` on Windows). Run `studytrails doctor` for
the exact location. Within it:

- `config.json`: provider address and model, without the API key.
- `notes/personal/SUBJECT/`: imported or pasted notes with unique filenames.
- `notes/python/` and `notes/java/`: bundled examples, copied only when missing.
- `data/study.sqlite3`: real progress; `data/demo.sqlite3`: offline demonstration.

Existing source checkouts retain their original `data/` and `notes/` directories.
Existing `.env` settings using `GROQ_API_KEY` and `GROQ_MODEL` work until you save a
new provider configuration. Saved configuration takes precedence. No database
migration or deletion is performed. `STUDYTRAIL_HOME` selects another storage root;
copying existing data there is a deliberate manual step, not automatic merging.

## How it works

The model can call three tools: `get_scores`, `search_notes`, and `create_quiz`.
Pydantic validates tool arguments. SQLite stores quizzes and actual submitted
answers. Python grades answers; the model cannot fabricate saved scores. Requests
are bounded to six model rounds and ten tool calls. Tool order is suggested by the
prompt, not enforced. The agent cannot execute generated code.

The source is intentionally small: `agent.py` contains the tool loop, `tools.py`
defines allowed actions, `notes.py` searches notes, `storage.py` stores results,
`cli.py` runs the terminal interface, and `onboarding.py`/`preferences.py` handle
setup and personal storage.

## Contributions welcome

Bug reports, clearer documentation, sample notes, and focused improvements are
welcome. Read [CONTRIBUTING.md](CONTRIBUTING.md). Please include steps to reproduce
bugs and never share API keys, private notes, or your personal database.

See the [user guide](docs/USER_GUIDE.md) for configuration and troubleshooting,
and the [release guide](docs/RELEASING.md) for packaging and publishing.

## Licence

MIT. See [LICENSE](LICENSE).
