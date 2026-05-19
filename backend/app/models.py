from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from .database import Base


class Highlight(Base):
    __tablename__ = "highlights"

    id = Column(Integer, primary_key=True, index=True)
    source_title = Column(String(255), nullable=False)
    source_type = Column(String(100), nullable=False)
    text = Column(Text, nullable=False)
    tags = Column(String(255), default="")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    cards = relationship("Card", back_populates="highlight", cascade="all, delete-orphan")


class Card(Base):
    __tablename__ = "cards"

    id = Column(Integer, primary_key=True, index=True)
    highlight_id = Column(Integer, ForeignKey("highlights.id"), nullable=False, index=True)
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    card_type = Column(String(64), default="short_answer", nullable=False)
    difficulty = Column(String(32), default="medium", nullable=False)
    source_quote = Column(Text, default="", nullable=False)
    is_flagged = Column(Boolean, default=False, nullable=False)

    interval_days = Column(Integer, default=1, nullable=False)
    repetitions = Column(Integer, default=0, nullable=False)
    ease_factor = Column(Float, default=2.5, nullable=False)
    due_date = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_reviewed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    highlight = relationship("Highlight", back_populates="cards")
    review_logs = relationship("ReviewLog", back_populates="card", cascade="all, delete-orphan")


class ReviewLog(Base):
    __tablename__ = "review_logs"

    id = Column(Integer, primary_key=True, index=True)
    card_id = Column(Integer, ForeignKey("cards.id"), nullable=False, index=True)
    rating = Column(String(10), nullable=False)
    reviewed_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    prev_interval_days = Column(Integer, nullable=False)
    new_interval_days = Column(Integer, nullable=False)

    card = relationship("Card", back_populates="review_logs")
