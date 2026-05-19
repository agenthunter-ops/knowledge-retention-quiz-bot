from datetime import datetime

from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy.orm import Session

from .database import Base, engine, get_db
from .models import Card, Highlight, ReviewLog
from .schemas import CardOut, CardUpdate, HighlightCreate, HighlightOut, ReviewRequest
from .services.quiz_generator import generate_mock_cards, normalize_tags
from .services.scheduler import ScheduleState, schedule_next

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Knowledge Retention Quiz Bot API")


@app.post("/highlights", response_model=HighlightOut)
def create_highlight(payload: HighlightCreate, db: Session = Depends(get_db)):
    highlight = Highlight(
        source_title=payload.source_title,
        source_type=payload.source_type.value,
        text=payload.text,
        tags=normalize_tags(payload.tags),
    )
    db.add(highlight)
    db.flush()

    for q, a in generate_mock_cards(payload.text):
        db.add(Card(highlight_id=highlight.id, question=q, answer=a, due_date=datetime.utcnow()))

    db.commit()
    db.refresh(highlight)
    return HighlightOut(
        id=highlight.id,
        source_title=highlight.source_title,
        source_type=highlight.source_type,
        text=highlight.text,
        tags=highlight.tags.split(",") if highlight.tags else [],
        created_at=highlight.created_at,
    )


@app.get("/highlights", response_model=list[HighlightOut])
def list_highlights(db: Session = Depends(get_db)):
    highlights = db.query(Highlight).order_by(Highlight.created_at.desc()).all()
    return [
        HighlightOut(
            id=h.id,
            source_title=h.source_title,
            source_type=h.source_type,
            text=h.text,
            tags=h.tags.split(",") if h.tags else [],
            created_at=h.created_at,
        )
        for h in highlights
    ]


@app.get("/cards", response_model=list[CardOut])
def list_cards(db: Session = Depends(get_db)):
    return db.query(Card).order_by(Card.created_at.desc()).all()


@app.get("/cards/due", response_model=list[CardOut])
def get_due_cards(db: Session = Depends(get_db)):
    return db.query(Card).filter(Card.due_date <= datetime.utcnow(), Card.is_flagged.is_(False)).order_by(Card.due_date.asc()).all()


@app.post("/reviews/{card_id}", response_model=CardOut)
def review_card(card_id: int, payload: ReviewRequest, db: Session = Depends(get_db)):
    card = db.get(Card, card_id)
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")

    previous_interval = card.interval_days
    state = ScheduleState(interval_days=card.interval_days, repetitions=card.repetitions, ease_factor=card.ease_factor)
    new_state, due_date = schedule_next(state, payload.rating.value)

    card.interval_days = new_state.interval_days
    card.repetitions = new_state.repetitions
    card.ease_factor = new_state.ease_factor
    card.last_reviewed_at = datetime.utcnow()
    card.due_date = due_date

    db.add(
        ReviewLog(
            card_id=card.id,
            rating=payload.rating.value,
            prev_interval_days=previous_interval,
            new_interval_days=new_state.interval_days,
        )
    )

    db.commit()
    db.refresh(card)
    return card


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
