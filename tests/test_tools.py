import json

import pytest

from study_agent.notes import search_notes


def test_search_returns_source_and_avoids_irrelevant_passages(tools):
    (tools.notes_directory / "functions.md").write_text(
        "Functions return values.", encoding="utf-8"
    )
    results = search_notes(tools.notes_directory, "loops range")
    assert len(results) == 1
    assert results[0]["source"] == "loops.md"
    assert results[0]["line"] == 1
    assert search_notes(tools.notes_directory, "astronomy") == []


def test_invalid_quiz_cannot_be_persisted(tools, quiz):
    data = quiz.model_dump()
    data["questions"][0]["options"] = ["same"] * 4
    with pytest.raises(ValueError, match="distinct"):
        tools.execute("create_quiz", json.dumps(data))
    assert tools.store.pending_quizzes() == []


def test_unknown_and_forged_score_tools_are_rejected(tools):
    for name in ["save_result", "run_shell", "delete_file"]:
        with pytest.raises(ValueError, match="Unknown tool"):
            tools.execute(name, "{}")


def test_quiz_creation_returns_no_answer_key_and_is_limited(tools, quiz):
    result = tools.execute("create_quiz", quiz.model_dump_json())
    assert result["question_count"] == 3
    assert "questions" not in result
    assert tools.store.get_scores()["completed_quizzes"] == 0
    with pytest.raises(ValueError, match="Only one quiz"):
        tools.execute("create_quiz", quiz.model_dump_json())


@pytest.mark.parametrize(
    "arguments", ['{"query": ""}', '{"query": "loops", "path": "C:/"}', "no json"]
)
def test_invalid_search_arguments_fail_before_execution(tools, arguments):
    with pytest.raises(ValueError):
        tools.execute("search_notes", arguments)
