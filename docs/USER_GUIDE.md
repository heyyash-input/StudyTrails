# StudyTrail user guide

## Setup and storage

Provider 4 is DeepSeek (`https://api.deepseek.com`). Its suggested model is
`deepseek-flash`; press Enter to accept it or enter a current model ID from your
account. Both study requests and the optional connection test use non-thinking
mode with DeepSeek. See [DeepSeek's tool-calling guide](https://api-docs.deepseek.com/guides/tool_calls/).
An API key and any required account credit must be supplied by the user.

All yes/no prompts display `[y/n] (Enter = no)`. They accept y/yes and n/no,
case-insensitively, and reprompt for other input. Chat and `ask` render Markdown
headings, lists, and code examples, retaining note citations.

Run `studytrails` to open the menu, or `studytrails config` to configure AI directly.
Choose a provider preset or enter an OpenAI-compatible Chat Completions base URL.
Enter a model that supports function/tool calling and that your account can access.
Setup displays the API destination before requesting the key. HTTPS is required
for remote endpoints; HTTP is accepted only for localhost development.

Settings go into `config.json`; keys go into a supported OS credential store.
StudyTrail supports the keyring Windows, macOS, Secret Service, KWallet, and
libsecret backends. Availability depends on your OS/session. It rejects plaintext
fallbacks. For a headless machine, inject `STUDYTRAIL_API_KEY` through your environment.
Never put real keys in shell commands that you plan to share or commit.

Configuration precedence:

1. If the storage root has `config.json`, its endpoint/model are used. An explicit
   `STUDYTRAIL_API_KEY` overrides the stored credential for that configuration.
2. Without saved configuration, `STUDYTRAIL_BASE_URL`, `STUDYTRAIL_MODEL`, and
   `STUDYTRAIL_API_KEY` configure a custom endpoint.
3. Otherwise legacy `GROQ_API_KEY` and `GROQ_MODEL` are supported. A source checkout
   reads its own `.env`, without overriding existing environment variables.

A saved configuration never borrows a legacy key for a different endpoint. Clear
an old `STUDYTRAIL_API_KEY` environment override before switching providers if it
belongs to the previous provider. Provider changes do not erase earlier credentials
from the operating system's credential manager; remove obsolete entries there.
Keys are scoped by storage root and API endpoint, so changing `STUDYTRAIL_HOME`
requires configuring credentials for the new location.

Run `studytrails doctor` to find storage paths. Installed wheels use personal
application data. Editable/source installations keep data beside the project.
`STUDYTRAIL_HOME` overrides either mode. No settings are loaded from an arbitrary
current working directory in an installed release.

## Notes and subjects

Use `studytrails notes-add` or Manage notes in the menu. Paste text (finish with
`.done`) or import a UTF-8 `.md`/`.txt` file. Imports copy the contents and leave the
original file untouched. Each note receives a unique filename; existing notes are
not overwritten. Subject/title input accepts 1-50 ASCII letters, digits, spaces,
and hyphens; spaces normalise to hyphens. Use `java`, `python`, or `world-history`.

Search a subject with `studytrails notes "inheritance" --subject java` and start
chat with `studytrails chat --subject java`. Subject-specific search reads only
`notes/SUBJECT/` and `notes/personal/SUBJECT/`. Older notes in the root or `private/`
remain accessible in all-subject mode; move them into a subject directory if you
want them included in that subject's searches.

Search uses shared keyword counts, up to four passages, overlapping windows of
24 lines with an 18-line step, and a 2,500-character passage cap. Files over
200,000 bytes are skipped. No indexing step is needed. PDF/OCR, Word import,
semantic embeddings, and automatic factual verification are not implemented.

The coach is instructed to cite notes as `[filename:line]` and distinguish general
knowledge when no notes match. These are model instructions, not a guarantee.
Relevant excerpts, score summaries, and recent chat messages may be sent to your
selected provider. Personal note files are Git-ignored in the source checkout.

## Progress, backups, and compatibility

SQLite stores pending quizzes and completed attempts. Quiz topic labels include
the selected subject for new subject-specific requests. Scores show all topics,
weakest first. Old topic labels and results are preserved. Demo scores are separate.
Chat memory holds only the most recent three completed turns and is not persisted.

Close the app before copying the `data/` and `notes/` folders to a backup. You may
also back up `config.json`; it contains no key. Configure credentials separately
on a new machine. Do not share personal databases publicly.

The original `python -m study_agent` commands remain supported. `notes QUERY` is
still a local search command; `notes-add` opens the interactive notes manager.
Offline commands do not make provider API requests.

## Troubleshooting

- **Command not found:** activate the environment used to install the package, or
  use `uv run studytrails` from the checkout. On Windows the existing environment
  can run `.\.venv\Scripts\studytrails.exe` directly.
- **401 / authentication failure:** run `studytrails config`; check that the key
  belongs to the displayed endpoint and inspect any environment-key override.
- **404 / model not found:** copy the current model ID from your provider and check
  account access. An incorrect base URL can also produce 404.
- **400 / unsupported parameters or tools:** choose a compatible Chat Completions
  model. Some providers implement only part of the protocol. Native non-compatible
  APIs require a separate integration; changing the key cannot fix this.
- **429 / quota:** wait for your provider's reset or inspect its plan. The app cannot
  determine whether a request is free. Each study turn can make several requests.
- **Credential store unavailable:** configure an OS-backed keyring or supply
  `STUDYTRAIL_API_KEY` via the environment; setup never saves a plaintext fallback.
- **Hidden input unavailable:** run setup in a real terminal or use an environment
  key. Piped setup does not fall back to visibly echoing a key.
- **No matching notes:** check subject, file type, UTF-8 encoding, size, and keywords.
- **Invalid config.json:** run `studytrails config` to replace provider settings.
  This does not modify notes or quiz databases.

The app reports provider status codes and request IDs without printing raw API
responses or headers. Share those identifiers and the model ID when reporting bugs,
not your API key.

[Back to README](../README.md)
