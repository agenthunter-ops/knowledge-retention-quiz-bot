# Knowledge Retention Quiz Bot (MVP)

A simple full-stack app that turns notes/highlights into quiz cards and schedules review with an SM-2-inspired algorithm.

## Features

- Add highlights/notes with source metadata.
- Persist note title, source type, note text, tags, and timestamps.
- Generate quiz cards with an LLM when `OPENAI_API_KEY` is available, with automatic fallback to the mock generator.
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
### 3) AI Configuration

Create a `.env` file in the repo root (you can copy from `.env.example`):

```bash
cp .env.example .env
```

Set your OpenAI key:

```bash
OPENAI_API_KEY=your_openai_api_key_here
```

Behavior:
- If `OPENAI_API_KEY` is set, the backend attempts LLM-based generation and creates exactly 3 cards per highlight.
- If `OPENAI_API_KEY` is missing or LLM generation fails, the backend falls back to the existing mock generator and still saves the highlight.
- Each generated card includes: `question`, `answer`, `card_type`, `difficulty`, and `source_quote`.


## API Endpoints (MVP)

- `POST /notes` create note + generate cards
- `GET /cards/due` list due cards
- `PATCH /cards/{id}` edit card question/answer
- `POST /cards/{id}/flag` flag card as bad
- `POST /cards/{id}/review` submit rating and reschedule

## Notes

- No authentication in MVP.
- No secrets are hardcoded.
- Quiz generation uses an LLM when configured and falls back to mock generation for resilience.
