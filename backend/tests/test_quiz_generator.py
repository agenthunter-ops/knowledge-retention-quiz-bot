from app.services.quiz_generator import generate_fallback_cards


def test_generator_does_not_produce_common_word_answers():
    cards = generate_fallback_cards("Habits compound over time. Testing scheduler transitions with enough words.")
    answers = {card["answer"].strip().lower() for card in cards}
    assert "with" not in answers
    assert "over" not in answers


def test_cards_include_explanation_and_source_quote_and_multiple_types():
    cards = generate_fallback_cards("Spaced repetition helps retention by adjusting review intervals based on performance.")
    assert len(cards) >= 2
    assert len({card["card_type"] for card in cards}) >= 2
    for card in cards:
        assert card["explanation"].strip()
        assert card["source_quote"].strip()
