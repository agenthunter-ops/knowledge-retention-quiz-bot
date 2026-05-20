import json
import logging
import os
import re
from collections import Counter
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


def _split_sentences(text: str) -> list[str]:
    return [s.strip() for s in re.split(r"[.!?]\s+", text.replace("\n", " ")) if s.strip()]


def _extract_key_phrases(text: str) -> list[str]:
    tokens = re.findall(r"[A-Za-z][A-Za-z\-]{2,}", text)
    freq = Counter(t.lower() for t in tokens if t.lower() not in BAD_ANSWERS)
    candidates = [term for term, _ in freq.most_common(8)]
    multi_word = re.findall(r"\b([A-Za-z]{3,}(?:\s+[A-Za-z]{3,}){1,3})\b", text)
    for phrase in multi_word:
        if any(w.lower() in BAD_ANSWERS for w in phrase.split()):
            continue
        if phrase.lower() not in candidates:
            candidates.append(phrase.lower())
    return candidates[:8]


def is_high_quality_card(card: dict) -> bool:
    question = str(card.get("question", "")).strip()
    answer = str(card.get("answer", "")).strip().lower()
    source_quote = str(card.get("source_quote", "")).strip()
    explanation = str(card.get("explanation", "")).strip()
    card_type = str(card.get("card_type", "")).strip()

    if len(question) < 20:
        return False
    if answer in BAD_ANSWERS:
        return False
    if len(answer) < 3:
        return False
    if not source_quote:
        return False
    if not explanation:
        return False
    if card_type not in CARD_TYPES:
        return False

    concept_tokens = {"why", "how", "tradeoff", "scenario", "concept", "because", "should", "impact"}
    if not any(token in question.lower() for token in concept_tokens) and len(question.split()) < 6:
        return False
    return True


def generate_fallback_cards(highlight_text: str) -> list[dict[str, str]]:
    sentences = _split_sentences(highlight_text)
    source = sentences[0] if sentences else highlight_text.strip()
    key_phrases = _extract_key_phrases(highlight_text)
    main_term = key_phrases[0] if key_phrases else "core concept"
    alt_term = key_phrases[1] if len(key_phrases) > 1 else main_term

    cards = [
        {
            "question": f"What is the core concept behind {main_term} in this highlight, and how would you explain it in practical terms?",
            "answer": f"{main_term.title()} is presented as a repeatable idea that should guide daily study behavior and improve retention through consistent review.",
            "card_type": "concept",
            "difficulty": "medium",
            "source_quote": source,
            "explanation": "This checks conceptual understanding instead of asking for exact wording.",
            "why_it_matters": "Learners need to internalize the idea to apply it across different study contexts.",
            "tags": "concept,understanding",
        },
        {
            "question": f"Why does the highlight imply that focusing on {alt_term} improves long-term learning outcomes?",
            "answer": "Because repeated, intentional practice reinforces recall pathways and reduces forgetting between sessions.",
            "card_type": "why_reasoning",
            "difficulty": "medium",
            "source_quote": source,
            "explanation": "This forces the learner to explain causal reasoning.",
            "why_it_matters": "Reasoning questions build transferable judgment, not rote recall.",
            "tags": "why,retention",
        },
        {
            "question": "A learner repeatedly misses the same card. What should the review system do next, and why?",
            "answer": "The scheduler should shorten the interval and resurface the card sooner so difficulty is addressed before forgetting compounds.",
            "card_type": "scenario_application",
            "difficulty": "medium",
            "source_quote": source,
            "explanation": "This evaluates practical application of spaced-repetition logic.",
            "why_it_matters": "Application skills are required to tune learning systems effectively.",
            "tags": "scenario,scheduling",
        },
    ]

    return [card for card in cards if is_high_quality_card(card)]


def generate_llm_cards(highlight_text: str) -> list[dict[str, str]]:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not set")

    client = OpenAI(api_key=api_key)
    prompt = (
        "Generate exactly 5 high-quality quiz cards from the highlight. "
        "Cards must use only these card_type values: concept, why_reasoning, scenario_application, tradeoff, cloze_key_term. "
        "Every object must include: question, answer, card_type, difficulty, source_quote, explanation, why_it_matters, tags. "
        "Do not use common-word answers like with, over, the, is, are, and, because, from, for. "
        "Questions must test understanding and practical reasoning. "
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
