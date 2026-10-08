from datetime import UTC, datetime, timedelta

from rivalry.rules import (
    before_deadline,
    brier,
    captain_slot_points,
    resolution_state,
    valid_probability,
)

NOW = datetime(2026, 10, 8, tzinfo=UTC)


def test_deadline_and_steps() -> None:
    assert before_deadline(NOW - timedelta(microseconds=1), NOW)
    assert not before_deadline(NOW, NOW)
    assert not before_deadline(NOW + timedelta(seconds=1), NOW)
    assert valid_probability(0) and valid_probability(100) and valid_probability(55)
    assert not valid_probability(51) and not valid_probability(-5) and not valid_probability(105)


def test_captain_promotion_and_brier() -> None:
    assert captain_slot_points(4, True, 9, True) == 8
    assert captain_slot_points(0, False, 9, True) == 18
    assert captain_slot_points(0, False, 0, False) == 0
    assert brier(80, True) == (0.8 - 1) ** 2
    assert brier(20, False) == 0.2**2


def test_void_and_confirmation_deadlock() -> None:
    deadline = NOW - timedelta(days=1)
    notice = NOW - timedelta(hours=72)
    assert resolution_state(NOW, deadline, False, True, None, None, {}) == "void"
    assert resolution_state(NOW, deadline, True, True, (10, 10), notice, {}) == "void"
    assert resolution_state(NOW, deadline, True, True, (10, 9), notice, {}) == "resolved"
    assert resolution_state(NOW - timedelta(seconds=1), deadline, True, True, (10, 9), notice, {}) == "awaiting_confirmation"
    assert resolution_state(NOW, deadline, True, True, (10, 9), notice, {"a": "dispute"}) == "disputed"
    assert resolution_state(NOW, deadline, True, True, (10, 9), None, {}) == "awaiting_notice"
    assert resolution_state(NOW, deadline, True, True, (10, 9), notice, {"a": "confirm", "b": "confirm"}) == "resolved"
