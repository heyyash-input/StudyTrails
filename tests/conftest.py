from copy import deepcopy

import pytest

from study_agent.demo import DEMO_QUIZ
from study_agent.models import Quiz
from study_agent.storage import Store
from study_agent.tools import StudyTools


@pytest.fixture
def quiz():
    return Quiz.model_validate(deepcopy(DEMO_QUIZ))


@pytest.fixture
def store(tmp_path):
    return Store(tmp_path / "study.sqlite3")


@pytest.fixture
def tools(store, tmp_path):
    notes = tmp_path / "notes"
    notes.mkdir()
    (notes / "loops.md").write_text("Python loops use range. break exits a loop.", encoding="utf-8")
    return StudyTools(store, notes)
