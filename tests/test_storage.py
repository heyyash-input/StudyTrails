import pytest

from study_agent.storage import Store


def test_timestamps_are_saved_in_utc(store, quiz):
    quiz_id = store.create_quiz(quiz)
    store.save_result(quiz_id, [1, 2, 3])
    with store.connect() as db:
        row = db.execute(
            (
                "SELECT q.created_at, a.completed_at FROM quizzes q "
                "JOIN attempts a ON q.id = a.quiz_id WHERE q.id = ?"
            ),
            (quiz_id,),
        ).fetchone()
    assert row["created_at"].endswith("+00:00")
    assert row["completed_at"].endswith("+00:00")


def test_scores_survive_restart_and_exclude_pending_quizzes(store, quiz):
    quiz_id = store.create_quiz(quiz)
    store.create_quiz(quiz)
    result = store.save_result(quiz_id, [1, 0, 3])
    assert result["score"] == 2
    assert result["percentage"] == 66.7
    reopened = Store(store.path)
    scores = reopened.get_scores()
    assert scores["completed_quizzes"] == 1
    assert scores["topics"][0]["correct"] == 2
    assert len(reopened.pending_quizzes()) == 1


@pytest.mark.parametrize("answers", [[1], [1, 2, 4], [True, 2, 3], ["B", 2, 3]])
def test_invalid_answers_do_not_record_progress(store, quiz, answers):
    quiz_id = store.create_quiz(quiz)
    with pytest.raises(ValueError):
        store.save_result(quiz_id, answers)
    assert store.get_scores()["completed_quizzes"] == 0


def test_duplicate_submission_cannot_inflate_progress(store, quiz):
    quiz_id = store.create_quiz(quiz)
    store.save_result(quiz_id, [1, 2, 3])
    with pytest.raises(ValueError, match="already completed"):
        store.save_result(quiz_id, [1, 2, 3])
    assert store.get_scores()["completed_quizzes"] == 1


def test_missing_quiz_is_a_clear_error(store):
    with pytest.raises(ValueError, match="does not exist"):
        store.get_quiz("missing")


def test_topic_scores_are_weighted_by_question_count(store, quiz):
    store.save_result(store.create_quiz(quiz), [1, 2, 3])
    shorter = quiz.model_copy(update={"questions": quiz.questions[:1]})
    store.save_result(store.create_quiz(shorter), [0])
    topic = store.get_scores()["topics"][0]
    assert topic["percentage"] == 75.0
    assert topic["attempts"] == 2


def test_demo_and_live_scores_are_separate(tmp_path, quiz):
    live = Store(tmp_path / "study.sqlite3")
    demo = Store(tmp_path / "demo.sqlite3")
    demo.save_result(demo.create_quiz(quiz), [1, 2, 3])
    assert live.get_scores()["completed_quizzes"] == 0
