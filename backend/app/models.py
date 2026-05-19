from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from .database import Base


class Note(Base):
    __tablename__ = "notes"

    id = Column(Integer, primary_key=True, index=True)
    source_title = Column(String(255), nullable=False)
    source_type = Column(String(100), nullable=False)
    note_text = Column(Text, nullable=False)
    tags = Column(String(255), default="")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    cards = relationship("Card", back_populates="note", cascade="all, delete-orphan")


class Card(Base):
    __tablename__ = "cards"

    id = Column(Integer, primary_key=True, index=True)
    note_id = Column(Integer, ForeignKey("notes.id"), nullable=False, index=True)
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    is_flagged = Column(Boolean, default=False, nullable=False)

    interval_days = Column(Integer, default=1, nullable=False)
    repetitions = Column(Integer, default=0, nullable=False)
    ease_factor = Column(Float, default=2.5, nullable=False)
    due_date = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_reviewed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    note = relationship("Note", back_populates="cards")
