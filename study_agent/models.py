"""Validation at the boundary between model-generated data and Python code."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, str_strip_whitespace=True)


class Question(StrictModel):
    prompt: str = Field(
        min_length=5, max_length=1000, description="The question text. Use the key 'prompt'."
    )
    options: list[str] = Field(min_length=4, max_length=4)
    correct_index: int = Field(ge=0, le=3)
    explanation: str = Field(min_length=5, max_length=1500)

    @field_validator("options")
    @classmethod
    def validate_options(cls, options: list[str]) -> list[str]:
        cleaned = [option.strip() for option in options]
        if any(not option or len(option) > 500 for option in cleaned):
            raise ValueError("Each option must contain 1 to 500 characters.")
        if len({option.casefold() for option in cleaned}) != 4:
            raise ValueError("The four answer options must be distinct.")
        return cleaned


class Quiz(StrictModel):
    topic: str = Field(min_length=2, max_length=100)
    difficulty: Literal["beginner", "intermediate", "advanced"]
    questions: list[Question] = Field(min_length=1, max_length=5)


class SearchNotes(StrictModel):
    query: str = Field(min_length=1, max_length=200)


class GetScores(StrictModel):
    pass
