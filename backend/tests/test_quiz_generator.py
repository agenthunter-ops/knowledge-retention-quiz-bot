from app.services.quiz_generator import generate_fallback_cards


def test_generator_never_creates_should_with_over_concepts():
    cards = generate_fallback_cards("The scheduler should improve review quality over time with enough history.")
    questions = " ".join(card["question"].lower() for card in cards)
    assert "core concept behind should" not in questions
    assert "core concept behind with" not in questions
    assert "core concept behind over" not in questions


def test_spaced_repetition_text_generates_difficult_cards_and_due_date_cards():
    text = (
        "Difficult cards should return sooner than easy cards. "
        "Each card stores review history and a next due date. "
        "Ratings AGAIN HARD GOOD EASY update intervals in an SM-2 inspired algorithm."
    )
    cards = generate_fallback_cards(text)
    questions = [card["question"].lower() for card in cards]

    assert any("difficult cards" in q and "reviewed sooner" in q for q in questions)
    assert any("review history" in q or "next due date" in q for q in questions)


def test_every_generated_card_has_required_metadata_fields():
    cards = generate_fallback_cards("Spaced repetition uses review history and next due date to adapt intervals.")
    assert cards
    for card in cards:
        assert card["source_quote"].strip()
        assert card["explanation"].strip()
        assert card["why_it_matters"].strip()
        assert card["card_type"].strip()
        assert card["difficulty"].strip()
