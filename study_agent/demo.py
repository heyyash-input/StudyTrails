"""Offline demonstration of the same tools; this is not a live AI response."""

import json

from .tools import StudyTools

DEMO_QUIZ = {
    "topic": "loops",
    "difficulty": "beginner",
    "questions": [
        {
            "prompt": "Which values does list(range(3)) contain?",
            "options": ["[1, 2, 3]", "[0, 1, 2]", "[0, 1, 2, 3]", "[3]"],
            "correct_index": 1,
            "explanation": "range(3) starts at 0 and stops before 3, producing 0, 1, and 2.",
        },
        {
            "prompt": (
                "What is total after this code?\ntotal = 0\nfor n in [2, 4, 6]:\n    total += n"
            ),
            "options": ["6", "3", "12", "0"],
            "correct_index": 2,
            "explanation": "The loop adds each number to total: 0 + 2 + 4 + 6 = 12.",
        },
        {
            "prompt": "What does break do inside a loop?",
            "options": [
                "Restarts the loop",
                "Skips only the current iteration",
                "Stops the entire Python interpreter",
                "Exits the innermost loop",
            ],
            "correct_index": 3,
            "explanation": "break exits the innermost loop. continue skips to its next iteration.",
        },
    ],
}


def prepare_demo(tools: StudyTools, trace) -> str:
    tools.created_quizzes.clear()
    trace("get_scores")
    tools.execute("get_scores", "{}")
    trace("search_notes")
    tools.execute("search_notes", json.dumps({"query": "loops range break"}))
    trace("create_quiz")
    result = tools.execute("create_quiz", json.dumps(DEMO_QUIZ))
    return result["quiz_id"]
