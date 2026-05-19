from dataclasses import dataclass
from datetime import datetime, timedelta


@dataclass
class ScheduleState:
    interval_days: int
    repetitions: int
    ease_factor: float


def schedule_next(state: ScheduleState, rating: str, now: datetime | None = None) -> tuple[ScheduleState, datetime]:
    """Update card schedule based on rating using interview-friendly SM-2 style rules."""
    now = now or datetime.utcnow()

    if rating == "AGAIN":
        new_state = ScheduleState(interval_days=1, repetitions=0, ease_factor=max(1.3, state.ease_factor - 0.2))
        return new_state, now + timedelta(days=1)

    repetitions = state.repetitions + 1
    ease_factor = state.ease_factor

    if rating == "HARD":
        ease_factor = max(1.3, ease_factor - 0.15)
        interval = max(1, round(state.interval_days * 1.2))
    elif rating == "GOOD":
        if repetitions == 1:
            interval = 1
        elif repetitions == 2:
            interval = 3
        else:
            interval = max(1, round(state.interval_days * ease_factor))
    elif rating == "EASY":
        ease_factor += 0.15
        if repetitions == 1:
            interval = 2
        else:
            interval = max(2, round(state.interval_days * ease_factor * 1.3))
    else:
        raise ValueError(f"Unsupported rating: {rating}")

    new_state = ScheduleState(interval_days=interval, repetitions=repetitions, ease_factor=ease_factor)
    return new_state, now + timedelta(days=interval)
