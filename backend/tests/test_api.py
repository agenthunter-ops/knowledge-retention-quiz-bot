from datetime import datetime, timedelta

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base, get_db
from app.main import app
from app.models import Card

SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)



def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


def setup_function():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


def test_create_highlight_creates_cards():
    response = client.post(
        "/highlights",
        json={
            "source_title": "Atomic Habits",
            "source_type": "book",
            "text": "Habits compound over time. Identity drives behavior.",
            "tags": ["Habits", "Productivity"],
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["source_title"] == "Atomic Habits"
    assert payload["tags"] == ["habits", "productivity"]

    due_cards = client.get("/cards/due")
    assert due_cards.status_code == 200
    assert len(due_cards.json()) >= 1


def test_get_due_cards_excludes_future_and_flagged_cards():
    highlight = client.post(
        "/highlights",
        json={"source_title": "Paper", "source_type": "article", "text": "A long enough sentence for card generation.", "tags": []},
    ).json()

    db = TestingSessionLocal()
    try:
        cards = db.query(Card).filter(Card.highlight_id == highlight["id"]).all()
        assert cards
        cards[0].due_date = datetime.utcnow() - timedelta(days=1)
        cards[0].is_flagged = False
        if len(cards) > 1:
            cards[1].due_date = datetime.utcnow() + timedelta(days=3)
            cards[1].is_flagged = False
        if len(cards) > 2:
            cards[2].due_date = datetime.utcnow() - timedelta(days=1)
            cards[2].is_flagged = True
        db.commit()
    finally:
        db.close()

    due_cards = client.get("/cards/due")
    assert due_cards.status_code == 200
    result = due_cards.json()
    assert len(result) == 1
    assert result[0]["is_flagged"] is False


def test_scheduler_updates_for_all_ratings():
    highlight = client.post(
        "/highlights",
        json={"source_title": "Course", "source_type": "certification", "text": "Testing scheduler transitions with enough words.", "tags": []},
    ).json()

    db = TestingSessionLocal()
    try:
        card = db.query(Card).filter(Card.highlight_id == highlight["id"]).first()
        card_id = card.id
    finally:
        db.close()

    baseline = client.get("/cards/due").json()[0]
    start_ef = baseline["ease_factor"]

    again = client.post(f"/reviews/{card_id}", json={"rating": "AGAIN"}).json()
    assert again["repetitions"] == 0
    assert again["interval_days"] == 1
    assert again["ease_factor"] <= start_ef

    hard = client.post(f"/reviews/{card_id}", json={"rating": "HARD"}).json()
    assert hard["repetitions"] == 1
    assert hard["interval_days"] >= 1

    good = client.post(f"/reviews/{card_id}", json={"rating": "GOOD"}).json()
    assert good["repetitions"] == 2
    assert good["interval_days"] >= 1

    easy = client.post(f"/reviews/{card_id}", json={"rating": "EASY"}).json()
    assert easy["repetitions"] == 3
    assert easy["interval_days"] >= 2
    assert easy["ease_factor"] >= good["ease_factor"]
