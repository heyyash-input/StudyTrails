"""SQLite persistence. Scores are calculated here, never supplied by an LLM."""

import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from .models import Quiz


class Store:
    def __init__(self, path: Path):
        path.parent.mkdir(parents=True, exist_ok=True)
        self.path = path
        with self.connect() as db:
            db.executescript("""
                CREATE TABLE IF NOT EXISTS quizzes (
                    id TEXT PRIMARY KEY,
                    content TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS attempts (
                    quiz_id TEXT PRIMARY KEY REFERENCES quizzes(id),
                    answers TEXT NOT NULL,
                    score INTEGER NOT NULL,
                    total INTEGER NOT NULL,
                    completed_at TEXT NOT NULL
                );
            """)

    @contextmanager
    def connect(self):
        db = sqlite3.connect(self.path)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA foreign_keys = ON")
        try:
            with db:
                yield db
        finally:
            db.close()

    def create_quiz(self, quiz: Quiz) -> str:
        quiz_id = uuid4().hex[:12]
        with self.connect() as db:
            db.execute(
                "INSERT INTO quizzes VALUES (?, ?, ?)",
                (quiz_id, quiz.model_dump_json(), datetime.now(timezone.utc).isoformat()),
            )
        return quiz_id

    def get_quiz(self, quiz_id: str) -> Quiz:
        with self.connect() as db:
            row = db.execute("SELECT content FROM quizzes WHERE id = ?", (quiz_id,)).fetchone()
        if row is None:
            raise ValueError(f"Quiz '{quiz_id}' does not exist in this mode's database.")
        return Quiz.model_validate_json(row["content"])

    def is_completed(self, quiz_id: str) -> bool:
        with self.connect() as db:
            return (
                db.execute("SELECT 1 FROM attempts WHERE quiz_id = ?", (quiz_id,)).fetchone()
                is not None
            )

    def save_result(self, quiz_id: str, answers: list[int]) -> dict:
        quiz = self.get_quiz(quiz_id)
        if len(answers) != len(quiz.questions):
            raise ValueError("Answer every question before submitting the quiz.")
        if any(type(answer) is not int or not 0 <= answer <= 3 for answer in answers):
            raise ValueError("Answers must be option indexes from 0 to 3.")
        correct = [
            answer == question.correct_index
            for answer, question in zip(answers, quiz.questions, strict=True)
        ]
        score = sum(correct)
        try:
            with self.connect() as db:
                db.execute(
                    "INSERT INTO attempts VALUES (?, ?, ?, ?, ?)",
                    (
                        quiz_id,
                        json.dumps(answers),
                        score,
                        len(answers),
                        datetime.now(timezone.utc).isoformat(),
                    ),
                )
        except sqlite3.IntegrityError as exc:
            raise ValueError(
                "This quiz is already completed. Create a new quiz to practise again."
            ) from exc
        return {
            "quiz_id": quiz_id,
            "topic": quiz.topic,
            "score": score,
            "total": len(answers),
            "percentage": round(score / len(answers) * 100, 1),
            "correct": correct,
        }

    def get_scores(self) -> dict:
        with self.connect() as db:
            rows = db.execute("""
                SELECT q.content, a.score, a.total, a.completed_at
                FROM attempts a JOIN quizzes q ON q.id = a.quiz_id
                ORDER BY a.completed_at DESC
            """).fetchall()
        topics: dict[str, dict] = {}
        for row in rows:
            topic = json.loads(row["content"])["topic"].strip().casefold()
            item = topics.setdefault(
                topic, {"topic": topic, "attempts": 0, "correct": 0, "total": 0}
            )
            item["attempts"] += 1
            item["correct"] += row["score"]
            item["total"] += row["total"]
        for item in topics.values():
            item["percentage"] = round(item["correct"] / item["total"] * 100, 1)
        return {
            "completed_quizzes": len(rows),
            "topics": sorted(topics.values(), key=lambda item: item["percentage"]),
            "recent": [
                {
                    "topic": json.loads(row["content"])["topic"],
                    "score": row["score"],
                    "total": row["total"],
                    "completed_at": row["completed_at"],
                }
                for row in rows[:5]
            ],
        }

    def pending_quizzes(self) -> list[dict]:
        with self.connect() as db:
            rows = db.execute("""
                SELECT q.id, q.content FROM quizzes q
                LEFT JOIN attempts a ON q.id = a.quiz_id
                WHERE a.quiz_id IS NULL ORDER BY q.created_at DESC LIMIT 10
            """).fetchall()
        return [{"id": row["id"], "topic": json.loads(row["content"])["topic"]} for row in rows]
