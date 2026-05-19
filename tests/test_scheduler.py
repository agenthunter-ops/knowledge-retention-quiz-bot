from datetime import datetime

from backend.app.scheduler import ScheduleState, schedule_next


def test_again_resets_repetitions_and_interval():
    state = ScheduleState(interval_days=5, repetitions=3, ease_factor=2.5)
    new_state, due_date = schedule_next(state, "AGAIN", now=datetime(2026, 1, 1))
    assert new_state.interval_days == 1
    assert new_state.repetitions == 0
    assert new_state.ease_factor == 2.3
    assert due_date == datetime(2026, 1, 2)


def test_good_transitions_first_two_steps_then_multiplies():
    initial = ScheduleState(interval_days=1, repetitions=0, ease_factor=2.5)
    step1, _ = schedule_next(initial, "GOOD", now=datetime(2026, 1, 1))
    assert step1.interval_days == 1
    assert step1.repetitions == 1

    step2, _ = schedule_next(step1, "GOOD", now=datetime(2026, 1, 2))
    assert step2.interval_days == 3
    assert step2.repetitions == 2

    step3, _ = schedule_next(step2, "GOOD", now=datetime(2026, 1, 3))
    assert step3.interval_days == 8


def test_easy_boosts_interval_and_ease():
    state = ScheduleState(interval_days=4, repetitions=2, ease_factor=2.5)
    new_state, due_date = schedule_next(state, "EASY", now=datetime(2026, 1, 1))
    assert new_state.repetitions == 3
    assert new_state.ease_factor == 2.65
    assert new_state.interval_days == 14
    assert due_date == datetime(2026, 1, 15)
