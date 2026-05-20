import json
import logging
import os
import re
from typing import Iterable

from openai import OpenAI

logger = logging.getLogger(__name__)

CARD_TYPES = {
    "concept",
    "why_reasoning",
    "scenario_application",
    "tradeoff",
    "cloze_key_term",
}

BAD_ANSWERS = {
    "with",
    "over",
    "the",
    "is",
    "are",
    "and",
    "or",
    "to",
    "from",
    "for",
    "of",
    "in",
    "on",
    "a",
    "an",
    "by",
    "as",
    "at",
    "because",
}

CONCEPT_STOPWORDS = {
    "should", "would", "could", "can", "may", "might", "must", "the", "this", "that",
    "with", "over", "under", "because", "from", "into", "enough", "helps", "improves",
    "important", "good", "bad", "review", "time", "system", "card",
}

BLOCKED_QUESTION_PATTERNS = {
    "core concept behind should",
    "core concept behind would",
    "core concept behind could",
}


def _split_sentences(text: str) -> list[str]:
    return [s.strip() for s in re.split(r"[.!?]\s+", text.replace("\n", " ")) if s.strip()]


def _contains_any(text: str, terms: set[str]) -> bool:
    lowered = text.lower()
    return any(term in lowered for term in terms)


def _theme_cards(source_quote: str, highlight_text: str) -> list[dict[str, str]]:
    text = highlight_text.lower()
    cards: list[dict[str, str]] = []

    if ("difficult cards" in text or "easy cards" in text or ("difficult" in text and "easy" in text)):
        cards.append(
            {
                "question": "Why should difficult cards be reviewed sooner than easy cards?",
                "answer": "Difficult cards represent weaker memories and need shorter review intervals before the learner forgets them.",
                "card_type": "why_reasoning",
                "difficulty": "medium",
                "source_quote": source_quote,
                "explanation": "This connects difficulty signals to adaptive scheduling behavior.",
                "why_it_matters": "It ensures the learner spends more effort where forgetting risk is highest.",
                "tags": "difficulty,adaptive-scheduling",
            }
        )

    if ("review history" in text or "next due date" in text or "due date" in text):
        cards.append(
            {
                "question": "What data should every spaced repetition card store to support adaptive scheduling?",
                "answer": "It should store review history, difficulty, last reviewed date, interval, and next due date.",
                "card_type": "concept",
                "difficulty": "medium",
                "source_quote": source_quote,
                "explanation": "This tests understanding of the data model that powers review timing decisions.",
                "why_it_matters": "Without this data, the scheduler cannot personalize future review intervals.",
                "tags": "data-model,scheduler",
            }
        )

    if all(term in text for term in ["again", "hard", "good", "easy"]):
        cards.append(
            {
                "question": "How do recall ratings like AGAIN, HARD, GOOD, and EASY affect the next review date?",
                "answer": "Lower ratings shorten the interval and schedule an earlier review, while higher ratings increase the interval.",
                "card_type": "scenario_application",
                "difficulty": "medium",
                "source_quote": source_quote,
                "explanation": "This checks whether learners understand how performance feedback updates scheduling.",
                "why_it_matters": "Rating-driven scheduling is the core loop that improves long-term retention.",
                "tags": "ratings,intervals",
            }
        )

    if ("sm-2" in text or "sm2" in text):
        cards.append(
            {
                "question": "Why is an SM-2 inspired algorithm useful for an MVP spaced repetition app?",
                "answer": "It is simple, explainable, and updates intervals based on recall quality without heavy implementation complexity.",
                "card_type": "tradeoff",
                "difficulty": "medium",
                "source_quote": source_quote,
                "explanation": "This frames SM-2 as a product tradeoff between sophistication and practical implementation.",
                "why_it_matters": "Teams can ship a reliable scheduler quickly while keeping behavior transparent.",
                "tags": "sm-2,mvp,tradeoff",
            }
        )

    return cards


def is_high_quality_card(card: dict) -> bool:
    question = str(card.get("question", "")).strip()
    answer = str(card.get("answer", "")).strip().lower()
    source_quote = str(card.get("source_quote", "")).strip()
    explanation = str(card.get("explanation", "")).strip()
    why_it_matters = str(card.get("why_it_matters", "")).strip()
    card_type = str(card.get("card_type", "")).strip()

    if len(question) < 20:
        return False
    if any(pattern in question.lower() for pattern in BLOCKED_QUESTION_PATTERNS):
        return False
    if answer in BAD_ANSWERS:
        return False
    if len(answer.split()) < 8:
        return False
    if not source_quote or not explanation or not why_it_matters:
        return False
    if card_type not in CARD_TYPES:
        return False

    concept_match = re.search(r"core concept behind\s+([a-z\-]+)", question.lower())
    if concept_match and concept_match.group(1) in CONCEPT_STOPWORDS:
        return False

    concept_signals = {"difficult cards", "easy cards", "review history", "next review", "due date", "again", "hard", "good", "easy", "sm-2", "interval"}
    if not _contains_any(question, concept_signals) and card_type in {"concept", "tradeoff", "scenario_application"}:
        return False

    return True


def generate_fallback_cards(highlight_text: str) -> list[dict[str, str]]:
    sentences = _split_sentences(highlight_text)
    source_quote = sentences[0] if sentences else highlight_text.strip()

    cards = _theme_cards(source_quote=source_quote, highlight_text=highlight_text)

    if len(cards) < 2:
        cards.extend(
            [
                {
                    "question": "Why does spaced repetition use increasing intervals instead of fixed daily review?",
                    "answer": "Increasing intervals reinforce recall near the forgetting curve while avoiding unnecessary reviews for stable memories.",
                    "card_type": "why_reasoning",
                    "difficulty": "medium",
                    "source_quote": source_quote,
                    "explanation": "This tests conceptual understanding of interval expansion.",
                    "why_it_matters": "It connects scheduler design to efficient long-term retention.",
                    "tags": "spaced-repetition,intervals",
                },
                {
                    "question": "A card is answered incorrectly twice. What should happen to its next due date?",
                    "answer": "The next due date should move sooner by reducing the interval so the weak memory is reinforced before decay.",
                    "card_type": "scenario_application",
                    "difficulty": "medium",
                    "source_quote": source_quote,
                    "explanation": "This checks practical application of adaptive scheduling behavior.",
                    "why_it_matters": "It validates understanding of how systems respond to low recall quality.",
                    "tags": "weak-memories,next-due-date",
                },
            ]
        )

    unique_cards = []
    seen_questions = set()
    for card in cards:
        if card["question"] in seen_questions:
            continue
        seen_questions.add(card["question"])
        if is_high_quality_card(card):
            unique_cards.append(card)

    return unique_cards[:5]


def generate_llm_cards(highlight_text: str) -> list[dict[str, str]]:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not set")

    client = OpenAI(api_key=api_key)
    prompt = (
        "Generate exactly 5 high-quality quiz cards from the highlight. "
        "Cards must use only these card_type values: concept, why_reasoning, scenario_application, tradeoff, cloze_key_term. "
        "Every object must include: question, answer, card_type, difficulty, source_quote, explanation, why_it_matters, tags. "
        "Never create concept questions around modal/common words (should, would, could, with, over, helps, improves). "
        "Answers must be at least 8 words and questions must test practical understanding. "
        "Return strict JSON array only."
    )

    completion = client.responses.create(
        model="gpt-4.1-mini",
        input=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": f"HIGHLIGHT:\n{highlight_text}"},
        ],
        max_output_tokens=1200,
    )

    cards = json.loads(completion.output_text)
    if not isinstance(cards, list):
        raise ValueError("LLM output is not a list")

    required_fields = {"question", "answer", "card_type", "difficulty", "source_quote", "explanation", "why_it_matters", "tags"}
    normalized_cards: list[dict[str, str]] = []
    for card in cards:
        if not isinstance(card, dict) or not required_fields.issubset(card.keys()):
            continue
        normalized = {k: str(card[k]).strip() for k in required_fields}
        if is_high_quality_card(normalized):
            normalized_cards.append(normalized)

    if len(normalized_cards) < 3:
        raise ValueError("Not enough high-quality cards from LLM")

    return normalized_cards[:5]


def generate_cards_with_fallback(highlight_text: str) -> list[dict[str, str]]:
    if not os.getenv("OPENAI_API_KEY"):
        return generate_fallback_cards(highlight_text)

    try:
        cards = generate_llm_cards(highlight_text)
        if len({card["card_type"] for card in cards}) < 2:
            raise ValueError("Insufficient card type diversity")
        return cards
    except Exception:
        logger.exception("LLM generation failed; using fallback card generator")
        return generate_fallback_cards(highlight_text)


def normalize_tags(tags: Iterable[str]) -> str:
    return ",".join(sorted({t.strip().lower() for t in tags if t.strip()}))
