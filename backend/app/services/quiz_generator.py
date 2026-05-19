from typing import Iterable


def generate_mock_cards(highlight_text: str) -> list[tuple[str, str]]:
    """Create lightweight quiz cards from a highlight.

    The function is intentionally deterministic so interviewers can follow the logic.
    """
    sentences = [s.strip() for s in highlight_text.replace("\n", " ").split(".") if s.strip()]
    cards: list[tuple[str, str]] = []

    for sentence in sentences[:3]:
        words = sentence.split()
        if len(words) < 4:
            continue
        pivot = len(words) // 2
        answer = words[pivot]
        question = "Fill in the blank: " + " ".join(words[:pivot] + ["____"] + words[pivot + 1 :])
        cards.append((question, answer))

    if not cards and highlight_text.strip():
        cards.append(("What is the main idea of this highlight?", highlight_text.strip()[:120]))

    return cards


def normalize_tags(tags: Iterable[str]) -> str:
    return ",".join(sorted({t.strip().lower() for t in tags if t.strip()}))
