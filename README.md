# Knowledge Retention Quiz Bot (MVP)

A simple full-stack app that turns notes/highlights into quiz cards and schedules review with an SM-2-inspired algorithm.

## Features

- Add highlights/notes with source metadata.
- Persist note title, source type, note text, tags, and timestamps.
- Generate quiz cards using a **mock** generator (no LLM dependency).
- List due cards.
- Reveal answer.
- Rate recall (`AGAIN`, `HARD`, `GOOD`, `EASY`) to schedule next due date.
- Edit AI-generated cards.
- Flag bad cards.

## Tech Stack

- Backend: FastAPI + SQLAlchemy + SQLite
- Frontend: React + Vite
- Tests: pytest

## Project Structure

- `backend/app/main.py` API endpoints
- `backend/app/models.py` SQLAlchemy models
- `backend/app/scheduler.py` spaced-repetition logic
- `backend/app/quiz_generator.py` mock quiz generation
- `frontend/src/App.jsx` basic MVP UI
- `tests/test_scheduler.py` scheduler unit tests

## Setup

### 1) Backend

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
uvicorn backend.app.main:app --reload
```

Backend runs at `http://localhost:8000`.

### 2) Frontend

In a new terminal:

```bash
cd frontend
npm install
npm run dev
```

Frontend runs at `http://localhost:5173`.

## API Endpoints (MVP)

- `POST /notes` create note + generate cards
- `GET /cards/due` list due cards
- `PATCH /cards/{id}` edit card question/answer
- `POST /cards/{id}/flag` flag card as bad
- `POST /cards/{id}/review` submit rating and reschedule

## Notes

- No authentication in MVP.
- No secrets are hardcoded.
- Quiz generation is intentionally mocked for iteration speed and reviewability.
