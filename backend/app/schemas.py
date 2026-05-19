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


class HighlightCreate(BaseModel):
    source_title: str = Field(min_length=1)
    source_type: SourceType
    text: str = Field(min_length=1)
    tags: list[str] = []


class HighlightOut(BaseModel):
    id: int
    source_title: str
    source_type: str
    text: str
    tags: list[str]
    created_at: datetime


class CardOut(BaseModel):
    id: int
    highlight_id: int
    question: str
    answer: str
    card_type: str
    difficulty: str
    source_quote: str
    explanation: str
    why_it_matters: str
    tags: str
    is_flagged: bool
    due_date: datetime
    interval_days: int
    repetitions: int
    ease_factor: float


class CardUpdate(BaseModel):
    question: str
    answer: str


class ReviewRequest(BaseModel):
    rating: Rating
