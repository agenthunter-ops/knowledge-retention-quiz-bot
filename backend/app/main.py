from datetime import datetime

from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy.orm import Session

from .database import Base, engine, get_db
from .models import Card, Note
from .quiz_generator import generate_mock_cards, normalize_tags
from .scheduler import ScheduleState, schedule_next
from .schemas import CardOut, CardUpdate, NoteCreate, NoteOut, ReviewRequest

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Knowledge Retention Quiz Bot API")


@app.post("/notes", response_model=NoteOut)
def create_note(payload: NoteCreate, db: Session = Depends(get_db)):
    note = Note(
        source_title=payload.source_title,
        source_type=payload.source_type.value,
        note_text=payload.note_text,
        tags=normalize_tags(payload.tags),
    )
    db.add(note)
    db.flush()

    for q, a in generate_mock_cards(payload.note_text):
        db.add(Card(note_id=note.id, question=q, answer=a, due_date=datetime.utcnow()))

    db.commit()
    db.refresh(note)
    return NoteOut(
        id=note.id,
        source_title=note.source_title,
        source_type=note.source_type,
        note_text=note.note_text,
        tags=note.tags.split(",") if note.tags else [],
        created_at=note.created_at,
    )


@app.get("/cards/due", response_model=list[CardOut])
def get_due_cards(db: Session = Depends(get_db)):
    return db.query(Card).filter(Card.due_date <= datetime.utcnow(), Card.is_flagged.is_(False)).order_by(Card.due_date.asc()).all()


@app.patch("/cards/{card_id}", response_model=CardOut)
def edit_card(card_id: int, payload: CardUpdate, db: Session = Depends(get_db)):
    card = db.get(Card, card_id)
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")
    card.question = payload.question
    card.answer = payload.answer
    db.commit()
    db.refresh(card)
    return card


@app.post("/cards/{card_id}/flag", response_model=CardOut)
def flag_card(card_id: int, db: Session = Depends(get_db)):
    card = db.get(Card, card_id)
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")
    card.is_flagged = True
    db.commit()
    db.refresh(card)
    return card


@app.post("/cards/{card_id}/review", response_model=CardOut)
def review_card(card_id: int, payload: ReviewRequest, db: Session = Depends(get_db)):
    card = db.get(Card, card_id)
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")

    state = ScheduleState(interval_days=card.interval_days, repetitions=card.repetitions, ease_factor=card.ease_factor)
    new_state, due_date = schedule_next(state, payload.rating.value)

    card.interval_days = new_state.interval_days
    card.repetitions = new_state.repetitions
    card.ease_factor = new_state.ease_factor
    card.last_reviewed_at = datetime.utcnow()
    card.due_date = due_date

    db.commit()
    db.refresh(card)
    return card
