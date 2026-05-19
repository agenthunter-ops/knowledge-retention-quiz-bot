from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class SourceType(str, Enum):
    BOOK = "book"
    ARTICLE = "article"
    PDF = "pdf"
    CERTIFICATION = "certification"
    OTHER = "other"


class Rating(str, Enum):
    AGAIN = "AGAIN"
    HARD = "HARD"
    GOOD = "GOOD"
    EASY = "EASY"


class NoteCreate(BaseModel):
    source_title: str = Field(min_length=1)
    source_type: SourceType
    note_text: str = Field(min_length=1)
    tags: list[str] = []


class NoteOut(BaseModel):
    id: int
    source_title: str
    source_type: str
    note_text: str
    tags: list[str]
    created_at: datetime

    class Config:
        from_attributes = True


class CardOut(BaseModel):
    id: int
    note_id: int
    question: str
    answer: str
    is_flagged: bool
    due_date: datetime
    interval_days: int
    repetitions: int
    ease_factor: float

    class Config:
        from_attributes = True


class CardUpdate(BaseModel):
    question: str
    answer: str


class ReviewRequest(BaseModel):
    rating: Rating
