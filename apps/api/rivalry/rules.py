from datetime import UTC, datetime, timedelta


def utc_now() -> datetime:
    return datetime.now(UTC)


def as_utc(value: datetime) -> datetime:
    return value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)


def before_deadline(now: datetime, deadline: datetime) -> bool:
    return as_utc(now) < as_utc(deadline)


def valid_probability(value: int) -> bool:
    return 0 <= value <= 100 and value % 5 == 0


def brier(probability_pct: int, won: bool) -> float:
    return (probability_pct / 100 - int(won)) ** 2


def captain_slot_points(
    captain_points: int, captain_played: bool, vice_points: int, vice_played: bool, multiplier: int = 2
) -> int:
    if captain_played:
        return captain_points * multiplier
    if vice_played:
        return vice_points * multiplier
    return 0


def resolution_state(
    now: datetime,
    deadline: datetime,
    has_a: bool,
    has_b: bool,
    scores: tuple[int, int] | None,
    notice_at: datetime | None,
    actions: dict[str, str],
    manually_void: bool = False,
) -> str:
    if manually_void:
        return "void"
    if before_deadline(now, deadline):
        return "open"
    if not (has_a and has_b):
        return "void"
    if scores is None:
        return "awaiting_scores"
    if "dispute" in actions.values():
        return "disputed"
    if notice_at is None:
        return "awaiting_notice"
    if len(actions) == 2 or as_utc(now) >= as_utc(notice_at) + timedelta(hours=72):
        return "void" if scores[0] == scores[1] else "resolved"
    return "awaiting_confirmation"
