import uuid
from datetime import UTC, datetime, timedelta

import pytest
from fastapi import Depends, Request
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

import rivalry.api as api_module
from rivalry.auth import current_user
from rivalry.db import Base, get_db
from rivalry.models import User


@pytest.fixture
def flow(monkeypatch):
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    factory = sessionmaker(engine, expire_on_commit=False)
    ids = [uuid.uuid4() for _ in range(3)]
    with factory() as db:
        db.add_all([User(id=ids[i], email=f"person{i}@example.com") for i in range(3)])
        db.commit()

    def test_db():
        with factory() as db:
            yield db

    def test_user(request: Request, db: Session = Depends(test_db)):
        return db.get(User, ids[int(request.headers.get("X-Test-User", "0"))])

    api_module.app.dependency_overrides[get_db] = test_db
    api_module.app.dependency_overrides[current_user] = test_user
    monkeypatch.setattr(api_module, "send_score_notice", lambda _addresses, _duel: None)
    clock = [datetime(2026, 10, 8, 12, tzinfo=UTC)]
    monkeypatch.setattr(api_module, "utc_now", lambda: clock[0])
    yield TestClient(api_module.app), ids, clock, factory
    api_module.app.dependency_overrides.clear()
    engine.dispose()


def call(client, user, method, path, body=None):
    return client.request(method, path, headers={"X-Test-User": str(user)}, json=body)


def setup_duel(flow):
    client, ids, clock, _ = flow
    group = call(client, 0, "POST", "/groups", {"name": "Friends"}).json()
    code = group["invite_code"]
    assert call(client, 1, "POST", "/groups/join", {"invite_code": code}).status_code == 200
    deadline = clock[0] + timedelta(hours=1)
    duel = call(client, 0, "POST", f"/groups/{group['id']}/duels", {
        "member_a_id": str(ids[0]), "member_b_id": str(ids[1]),
        "claim_type": "gameweek_points", "gameweek": "GW1",
        "deadline_at": deadline.isoformat(),
    }).json()
    return group, duel, deadline


def test_private_access_deadline_revisions_and_no_show(flow):
    client, ids, clock, factory = flow
    group, duel, deadline = setup_duel(flow)
    path = f"/duels/{duel['id']}"
    assert call(client, 2, "GET", path).status_code == 404
    assert call(client, 1, "POST", path + "/submissions", {"probability_pct": 55}).status_code == 201
    assert call(client, 1, "POST", path + "/submissions", {"probability_pct": 65}).status_code == 201
    assert call(client, 0, "GET", path).json()["probabilities"] == {}
    assert call(client, 1, "GET", path).json()["probabilities"] == {str(ids[1]): 65}
    assert call(client, 0, "POST", path + "/submissions", {"probability_pct": 51}).status_code == 422
    clock[0] = deadline
    assert call(client, 0, "POST", path + "/submissions", {"probability_pct": 60}).status_code == 409
    assert call(client, 0, "GET", path).json()["status"] == "void"
    assert call(client, 1, "GET", f"/groups/{group['id']}/history").json()[str(ids[1])]["history"][0]["status"] == "void"
    with factory() as db:
        from rivalry.models import Submission
        assert len(db.query(Submission).all()) == 2


def test_score_dispute_correction_confirmation_and_stats(flow):
    client, ids, clock, _ = flow
    group, duel, deadline = setup_duel(flow)
    path = f"/duels/{duel['id']}"
    for user, probability in ((0, 80), (1, 60)):
        assert call(client, user, "POST", path + "/submissions", {"probability_pct": probability}).status_code == 201
    clock[0] = deadline
    assert call(client, 1, "POST", path + "/scores", {"score_a": 10, "score_b": 8,
                                                        "source_url": "https://fantasy.premierleague.com/"}).status_code == 403
    score = call(client, 0, "POST", path + "/scores", {"score_a": 10, "score_b": 8,
                                                        "source_url": "https://fantasy.premierleague.com/"}).json()
    assert score["status"] == "awaiting_confirmation"
    first = score["scores"][-1]["id"]
    assert call(client, 1, "POST", path + f"/scores/{first}/dispute",
                {"reason": "The entered gameweek value is wrong"}).json()["status"] == "disputed"
    corrected = call(client, 0, "POST", path + "/scores", {"score_a": 9, "score_b": 11,
                                                               "source_url": "https://fantasy.premierleague.com/"}).json()
    assert len(corrected["scores"]) == 2
    second = corrected["scores"][-1]["id"]
    assert call(client, 1, "POST", path + f"/scores/{first}/confirm").status_code == 409
    resolved = call(client, 1, "POST", path + f"/scores/{second}/confirm").json()
    assert resolved["status"] == "resolved"
    history = call(client, 0, "GET", f"/groups/{group['id']}/history").json()
    assert history[str(ids[0])]["sample_size"] == 1
    assert history[str(ids[0])]["mean_brier"] == pytest.approx(0.64)
    assert history[str(ids[1])]["mean_brier"] == pytest.approx(0.16)


def test_auto_confirmation_and_tie(flow):
    client, ids, clock, _ = flow
    group, duel, deadline = setup_duel(flow)
    path = f"/duels/{duel['id']}"
    for user in (0, 1):
        call(client, user, "POST", path + "/submissions", {"probability_pct": 50})
    clock[0] = deadline
    tie = call(client, 0, "POST", path + "/scores", {"score_a": 10, "score_b": 10,
                                                      "source_url": "https://fantasy.premierleague.com/"}).json()
    assert tie["status"] == "awaiting_confirmation"
    # Notice timestamp is the server's real UTC clock, so use its persisted value here.
    from rivalry.models import ScoreNotice
    with flow[3]() as db:
        notice_at = db.query(ScoreNotice).one().created_at.replace(tzinfo=UTC)
    clock[0] = notice_at + timedelta(hours=72)
    assert call(client, 1, "GET", path).json()["status"] == "void"
    stats = call(client, 0, "GET", f"/groups/{group['id']}/history").json()
    assert stats[str(ids[0])]["sample_size"] == 0


SOURCE = "https://fantasy.premierleague.com/"


def post_score(client, user, path, a, b):
    return call(client, user, "POST", path + "/scores", {"score_a": a, "score_b": b, "source_url": SOURCE})


def test_deadline_boundary_and_outsiders(flow):
    client, _, clock, _ = flow
    group, duel, deadline = setup_duel(flow)
    path = f"/duels/{duel['id']}"
    # A non-member cannot see the duel or its group.
    assert call(client, 2, "POST", path + "/submissions", {"probability_pct": 50}).status_code == 404
    assert call(client, 2, "GET", f"/groups/{group['id']}/duels").status_code == 404
    # One second before the deadline is accepted; the deadline instant is not.
    clock[0] = deadline - timedelta(seconds=1)
    assert call(client, 0, "POST", path + "/submissions", {"probability_pct": 50}).status_code == 201
    clock[0] = deadline
    assert call(client, 1, "POST", path + "/submissions", {"probability_pct": 50}).status_code == 409


def test_non_participant_member_cannot_submit(flow):
    client, *_ = flow
    group, duel, _ = setup_duel(flow)
    path = f"/duels/{duel['id']}"
    invite = call(client, 0, "POST", "/groups", {"name": "Second"}).json()["invite_code"]
    assert call(client, 2, "POST", "/groups/join", {"invite_code": invite}).status_code == 200
    # Person 2 belongs only to a different group, so this duel is invisible to them.
    assert call(client, 2, "POST", path + "/submissions", {"probability_pct": 50}).status_code == 404
    # A third member of the duel's own group can read the duel but not submit.
    assert call(client, 2, "POST", "/groups/join", {"invite_code": group["invite_code"]}).status_code == 200
    assert call(client, 2, "GET", path).status_code == 200
    assert call(client, 2, "POST", path + "/submissions", {"probability_pct": 50}).status_code == 403


def test_void_duel_blocks_submissions_and_stats(flow):
    client, ids, *_ = flow
    group, duel, _ = setup_duel(flow)
    path = f"/duels/{duel['id']}"
    assert call(client, 1, "POST", path + "/void", {"reason": "Wrong deadline"}).status_code == 403
    voided = call(client, 0, "POST", path + "/void", {"reason": "Wrong deadline"})
    assert voided.json()["status"] == "void"
    assert voided.json()["void_reason"] == "Wrong deadline"
    assert call(client, 0, "POST", path + "/void", {"reason": "Again please"}).status_code == 409
    assert call(client, 1, "POST", path + "/submissions", {"probability_pct": 50}).status_code == 409
    history = call(client, 0, "GET", f"/groups/{group['id']}/history").json()
    assert history[str(ids[0])]["sample_size"] == 0


def test_repeat_dispute_of_unchanged_score_is_rejected(flow):
    client, _, clock, _ = flow
    _, duel, deadline = setup_duel(flow)
    path = f"/duels/{duel['id']}"
    for user in (0, 1):
        call(client, user, "POST", path + "/submissions", {"probability_pct": 50})
    clock[0] = deadline
    first = post_score(client, 0, path, 10, 8).json()["scores"][-1]["id"]
    reason = {"reason": "The entered gameweek value is wrong"}
    assert call(client, 1, "POST", path + f"/scores/{first}/dispute", reason).json()["status"] == "disputed"
    # Admin reaffirms identical values: a new revision, but B may not dispute the same numbers again.
    second = post_score(client, 0, path, 10, 8).json()["scores"][-1]["id"]
    assert call(client, 1, "POST", path + f"/scores/{second}/dispute", reason).status_code == 409
    assert call(client, 1, "POST", path + f"/scores/{second}/confirm").json()["status"] == "resolved"


def test_72_hour_boundary(flow):
    client, _, clock, factory = flow
    _, duel, deadline = setup_duel(flow)
    path = f"/duels/{duel['id']}"
    for user in (0, 1):
        call(client, user, "POST", path + "/submissions", {"probability_pct": 50})
    clock[0] = deadline
    post_score(client, 0, path, 10, 8)
    from rivalry.models import ScoreNotice
    with factory() as db:
        notice_at = db.query(ScoreNotice).one().created_at.replace(tzinfo=UTC)
    clock[0] = notice_at + timedelta(hours=72) - timedelta(seconds=1)
    assert call(client, 1, "GET", path).json()["status"] == "awaiting_confirmation"
    clock[0] = notice_at + timedelta(hours=72)
    assert call(client, 1, "GET", path).json()["status"] == "resolved"
    # The window is closed: a late confirmation is refused.
    revision = call(client, 1, "GET", path).json()["scores"][-1]["id"]
    assert call(client, 1, "POST", path + f"/scores/{revision}/confirm").status_code == 409
