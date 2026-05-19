import json
import logging
import os
from typing import Iterable

from openai import OpenAI

logger = logging.getLogger(__name__)


def generate_mock_cards(highlight_text: str) -> list[dict[str, str]]:
    """Create lightweight quiz cards from a highlight.

    The function is intentionally deterministic so interviewers can follow the logic.
    """
    sentences = [s.strip() for s in highlight_text.replace("\n", " ").split(".") if s.strip()]
    cards: list[dict[str, str]] = []

    for sentence in sentences[:3]:
        words = sentence.split()
        if len(words) < 4:
            continue
        pivot = len(words) // 2
        answer = words[pivot]
        question = "Fill in the blank: " + " ".join(words[:pivot] + ["____"] + words[pivot + 1 :])
        cards.append(
            {
                "question": question,
                "answer": answer,
                "card_type": "fill_in_the_blank",
                "difficulty": "medium",
                "source_quote": sentence,
            }
        )

    if not cards and highlight_text.strip():
        cards.append(
            {
                "question": "What is the main idea of this highlight?",
                "answer": highlight_text.strip()[:120],
                "card_type": "short_answer",
                "difficulty": "easy",
                "source_quote": highlight_text.strip()[:220],
            }
        )

    return cards[:3]


def generate_llm_cards(highlight_text: str) -> list[dict[str, str]]:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not set")

    client = OpenAI(api_key=api_key)
    prompt = (
        "Generate exactly 3 quiz cards from the provided highlight. "
        "Use only facts from the highlight. Do not add external knowledge. "
        "Return strict JSON array with 3 objects and keys: "
        "question, answer, card_type, difficulty, source_quote."
    )

    completion = client.responses.create(
        model="gpt-4.1-mini",
        input=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": f"HIGHLIGHT:\n{highlight_text}"},
        ],
        max_output_tokens=800,
    )

    raw = completion.output_text
    cards = json.loads(raw)
    if not isinstance(cards, list) or len(cards) != 3:
        raise ValueError("LLM did not return exactly 3 cards")

    required_fields = {"question", "answer", "card_type", "difficulty", "source_quote"}
    normalized_cards: list[dict[str, str]] = []
    for card in cards:
        if not isinstance(card, dict) or not required_fields.issubset(card.keys()):
            raise ValueError("LLM card missing required fields")
        normalized_cards.append({k: str(card[k]).strip() for k in required_fields})

    return normalized_cards


def generate_cards_with_fallback(highlight_text: str) -> list[dict[str, str]]:
    if not os.getenv("OPENAI_API_KEY"):
        return generate_mock_cards(highlight_text)

    try:
        return generate_llm_cards(highlight_text)
    except Exception:
        logger.exception("LLM generation failed; using mock card generator")
        return generate_mock_cards(highlight_text)


def normalize_tags(tags: Iterable[str]) -> str:
    return ",".join(sorted({t.strip().lower() for t in tags if t.strip()}))
