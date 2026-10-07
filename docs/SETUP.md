# StudyTrail setup guide

This guide helps you install StudyTrail on a new computer. It is a terminal app:
you install it once, then run `studytrails` from PowerShell, Terminal, or a shell.

StudyTrail is free and MIT licensed. Live AI uses an API key from a compatible
provider. Your provider controls its own free allowance, usage limits, and charges.
You can use the offline demo without an API key.

## 1. Install Python

StudyTrail supports Python **3.10, 3.11, 3.12, 3.13, and 3.14**. Python 3.12 is
shown in the commands below; replace `3.12` with your installed version when you
want to use another supported release. The `openai` library used by StudyTrail
requires Python 3.10 or newer.

- **Windows:** Install Python from [python.org](https://www.python.org/downloads/).
  In the installer, enable **Add python.exe to PATH**. Then open a new PowerShell
  window and check `py --version`.
- **macOS:** Install Python 3.10–3.14 from [python.org](https://www.python.org/downloads/)
  or your preferred package manager. Check `python3.12 --version`.
- **Linux:** Install Python 3.10–3.14 and its `venv` support using your
  distribution's package manager. Check `python3.12 --version`.

## 2. Install StudyTrail in its own environment

An environment keeps StudyTrail's Python packages separate from other projects.
Choose the instructions for your operating system. Run the commands in the folder
where you want to keep this environment; create a folder first if needed.

### Windows PowerShell

```powershell
mkdir StudyTrail
cd StudyTrail
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install studytrails
studytrails
```

If PowerShell blocks activation, use this for the current terminal only, then
activate the environment again:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
.\.venv\Scripts\Activate.ps1
```

Or skip activation and run the installed command directly:

```powershell
.\.venv\Scripts\studytrails.exe
```

### macOS or Linux

```bash
mkdir StudyTrail
cd StudyTrail
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install studytrails
studytrails
```

If your system's `python3.12` command has another name, use the command for your
chosen supported Python version to create the environment.

### Optional: install uv

You can use [uv](https://docs.astral.sh/uv/getting-started/installation/) to
install StudyTrail as an isolated command-line tool. After installing uv, run:

```powershell
uv tool install studytrails
uv tool update-shell
```

On macOS or Linux, the commands are the same. Open a new terminal after
`uv tool update-shell`, then run `studytrails` from any folder. If the command
is still not found, follow uv's PATH instructions for your shell.

## 3. Set up an AI provider (optional)

The first run opens a welcome menu. Choose **Configure AI** to use live coaching.
You will need:

1. An API key from a provider you choose.
2. The provider's API address, if you choose a custom OpenAI-compatible endpoint.
3. A model ID that your provider account can access and that supports
   OpenAI-compatible Chat Completions with tool calling.

StudyTrail offers address presets for OpenAI and Groq. A preset only fills in the
provider address; it does not provide a key or guarantee every model will work.
For another compatible service, choose the custom endpoint option and enter its
API base URL and model ID. StudyTrail cannot use provider APIs with an incompatible
request format in this release.

The key prompt is hidden while you type. Paste the key only into that prompt. Do
not paste it into the provider number or model prompt, a command line, this guide,
or a public issue. Setup can make an optional small connection test; the request
may use provider quota or incur charges. Choose **No** to skip it.

StudyTrail stores API keys in a supported operating-system credential manager.
Provider usage and billing are controlled by the provider. Review your provider's
plan and limits before making live requests. Each study interaction may use more
than one request.

To configure later, run:

```text
studytrails config
```

## 4. Start studying

In the welcome menu, select **Start learning** to chat with the coach. Select
**Manage notes** to paste notes or import a UTF-8 `.txt` or `.md` file; choose a
subject such as `python`, `java`, or `biology`. When pasting, enter `.done` on a
line by itself to save the note. Then start learning and choose the same subject
to search those notes.

Try asking:

```text
Explain Java inheritance using my notes, then give me two beginner questions.
```

The app includes sample Python and Java notes. Notes are searched by keywords;
PDF and Word files are not supported. Note excerpts and study requests are sent to
the AI provider you configured. Avoid adding private information unless you are
comfortable sharing it with that provider.

If you want to try the app without an API key, choose **Offline demo** from the
menu. It runs a fixed Python quiz and stores demo results separately from your
regular progress. It is not a local AI model.

## 5. Run StudyTrail next time

For a virtual environment installation, open a new terminal, go to the folder
where you installed StudyTrail, activate `.venv`, then type `studytrails`:

```powershell
cd .\StudyTrail
.\.venv\Scripts\Activate.ps1
studytrails
```

The macOS/Linux activation command is `source .venv/bin/activate`. If you used
`uv tool install`, simply open a new terminal and type `studytrails`.

## 6. Find your notes and progress

Run this command from an activated environment or uv tool installation:

```text
studytrails doctor
```

It reports the local folder used for your settings, notes, and progress. Installed
releases store these under your operating-system application data directory.
Your progress belongs to your computer and is not automatically uploaded or
synchronized.

## Troubleshooting

- **`studytrails` is not recognized / command not found:** activate the same
  virtual environment where you installed it. With uv, open a new terminal after
  `uv tool update-shell` and check uv's PATH instructions.
- **Python version error:** use Python 3.10 through 3.14 and recreate the `.venv`
  with that version.
- **PowerShell says scripts are disabled:** use the current-terminal command in
  the Windows section above, then activate again.
- **401 / authentication failed:** run `studytrails config` and check that the key
  belongs to the displayed provider address. Never share the key in a support
  request.
- **404 / model not found:** check the exact model ID and that the account can use
  it. Also verify the provider address.
- **429 / quota exceeded:** check the provider's current plan, rate limit, or
  quota reset time.
- **Want to test without an API:** select **Offline demo** in the menu.

For more features and command details, see the
[user guide](USER_GUIDE.md) and [project README](../README.md).
