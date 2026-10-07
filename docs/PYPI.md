# StudyTrail

Learn a little. Practise with purpose. See your progress.

StudyTrail is a terminal AI study coach. Bring your own compatible provider API
key, add study notes, practise with quizzes, and track progress locally.

Requires Python 3.12 or 3.13. Install the latest release in an activated
environment with `python -m pip install --upgrade studytrails`, or install an
isolated CLI with `uv tool install --upgrade studytrails`. Run `studytrails` to
open the welcome menu.

Created by Yash Patil, a Python and AI learner. The project uses OpenAI's Python
SDK for compatible chat APIs. OpenAI created the GPT-OSS model family; the API host
may be another provider, such as Groq. Users may configure other model families.

## Features

- Interactive provider, model, and hidden API-key setup.
- OpenAI-compatible Chat Completions endpoints with tool-calling models.
- OpenAI and Groq address presets; custom compatible endpoints supported.
- Multi-subject coaching and subject-specific note retrieval.
- Paste notes or import UTF-8 `.md` and `.txt` files up to 200 KB.
- Multiple-choice quizzes, explanations, and local SQLite progress.
- A fixed offline Python quiz demo that needs no API key.
- Keys stored in supported operating-system credential stores, without a plaintext fallback.

## Commands

```text
studytrails
studytrails config
studytrails chat --subject java
studytrails notes-add
studytrails notes "inheritance" --subject java
studytrails scores
studytrails pending
studytrails demo
studytrails doctor
```

Run `studytrails doctor` to see the personal storage location. Existing source
checkouts retain their original data directories. Set `STUDYTRAIL_HOME` to choose
a different root. Machines without a usable OS credential store can supply
`STUDYTRAIL_API_KEY` through the environment.

The software is MIT-licensed. API costs and limits depend on your provider and plan;
StudyTrail cannot guarantee free API usage. Your prompts, retrieved note passages,
and score summaries may be sent to the configured provider. Notes are retrieved by
keywords, not used to train a model. AI answers and quiz keys may contain mistakes.
The app does not execute generated code. Native APIs with incompatible request
formats are not supported. A provider preset does not guarantee every model works.
