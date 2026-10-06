"""The explicit tool allowlist available to the language model."""

from pathlib import Path

from .models import GetScores, Quiz, SearchNotes
from .notes import search_notes
from .storage import Store

TOOL_MODELS = {"get_scores": GetScores, "search_notes": SearchNotes, "create_quiz": Quiz}
DESCRIPTIONS = {
    "get_scores": "Read actual saved quiz scores, weakest topics first, and recent attempts.",
    "search_notes": "Search local study notes by topic keywords. Returns passages with sources.",
    "create_quiz": (
        "Save a quiz for the learner to answer in the terminal. Supply 1 to 5 questions, "
        "Each question object must use these exact keys: prompt (the question text), "
        "options (exactly 4 distinct strings), correct_index (0-based integer), and explanation. "
        "Keep topic labels consistent with previous scores. This does not record a score."
    ),
}


def tool_definitions() -> list[dict]:
    return [
        {
            "type": "function",
            "function": {
                "name": name,
                "description": DESCRIPTIONS[name],
                "parameters": model.model_json_schema(),
            },
        }
        for name, model in TOOL_MODELS.items()
    ]


class StudyTools:
    def __init__(self, store: Store, notes_directory: Path):
        self.store = store
        self.notes_directory = notes_directory
        self.created_quizzes: list[str] = []

    def execute(self, name: str, arguments: str) -> dict:
        if name not in TOOL_MODELS:
            raise ValueError(f"Unknown tool: {name}")
        parsed = TOOL_MODELS[name].model_validate_json(arguments)
        if name == "get_scores":
            return self.store.get_scores()
        if name == "search_notes":
            return {"passages": search_notes(self.notes_directory, parsed.query)}
        if self.created_quizzes:
            raise ValueError("Only one quiz can be created per request. Finish this request now.")
        quiz_id = self.store.create_quiz(parsed)
        self.created_quizzes.append(quiz_id)
        return {
            "quiz_id": quiz_id,
            "topic": parsed.topic,
            "question_count": len(parsed.questions),
            "status": "ready_for_learner",
        }
