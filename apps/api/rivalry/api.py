import hashlib
import secrets
import uuid
from datetime import UTC

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from rivalry.auth import current_user, membership
from rivalry.config import settings
from rivalry.db import get_db
from rivalry.mail import send_score_notice
from rivalry.models import (
    Confirmation,
    Duel,
    Group,
    Membership,
    ScoreNotice,
    ScoreRevision,
    Submission,
    User,
    VoidEvent,
)
from rivalry.rules import before_deadline, brier, resolution_state, utc_now, valid_probability
from rivalry.schemas import (
    CreateDuel,
    CreateGroup,
    DisputeScore,
    EnterScore,
    JoinGroup,
    SubmitProbability,
    UpdateUsername,
    VoidDuel,
)

app = FastAPI(title="Rivalry Court API")
app.add_middleware(CORSMiddleware, allow_origins=[settings.web_url], allow_credentials=True,
                   allow_methods=["*"], allow_headers=["Authorization", "Content-Type"])


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/me")
def me(user: User = Depends(current_user)) -> dict:
    return {"id": str(user.id), "email": user.email, "username": user.username,
            "display_name": display_name(user)}


def display_name(user: User) -> str:
    return user.username or f"Player-{str(user.id)[:8]}"


@app.patch("/me")
def update_me(body: UpdateUsername, user: User = Depends(current_user), db: Session = Depends(get_db)) -> dict:
    profile = db.get(User, user.id)
    if profile is None:
        raise HTTPException(404, "Profile not found")
    profile.username = body.username
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(409, "Username is already taken") from exc
    return me(profile)


def invite_hash(code: str) -> str:
    return hashlib.sha256(code.strip().upper().encode()).hexdigest()


def group_data(group: Group, role: str, invite_code: str | None = None) -> dict:
    result = {"id": str(group.id), "name": group.name, "role": role}
    if invite_code:
        result["invite_code"] = invite_code
    return result


@app.post("/groups", status_code=201)
def create_group(body: CreateGroup, user: User = Depends(current_user), db: Session = Depends(get_db)) -> dict:
    code = secrets.token_urlsafe(12).upper()
    group = Group(name=body.name.strip(), invite_hash=invite_hash(code))
    db.add(group)
    db.flush()
    db.add(Membership(group_id=group.id, user_id=user.id, role="admin"))
    db.commit()
    return group_data(group, "admin", code)


@app.get("/groups")
def list_groups(user: User = Depends(current_user), db: Session = Depends(get_db)) -> list[dict]:
    rows = db.execute(select(Group, Membership.role).join(Membership, Membership.group_id == Group.id)
                      .where(Membership.user_id == user.id).order_by(Group.created_at.desc())).all()
    return [group_data(group, role) for group, role in rows]


@app.post("/groups/join")
def join_group(body: JoinGroup, user: User = Depends(current_user), db: Session = Depends(get_db)) -> dict:
    group = db.scalar(select(Group).where(Group.invite_hash == invite_hash(body.invite_code)))
    if group is None:
        raise HTTPException(404, "Invalid invite code")
    existing = db.scalar(select(Membership).where(Membership.group_id == group.id, Membership.user_id == user.id))
    if existing is None:
        db.add(Membership(group_id=group.id, user_id=user.id, role="member"))
        db.commit()
    return group_data(group, existing.role if existing else "member")


@app.post("/groups/{group_id}/invite-code")
def rotate_invite_code(
    group_id: uuid.UUID, user: User = Depends(current_user), db: Session = Depends(get_db)
) -> dict:
    membership(db, group_id, user.id, admin=True)
    group = db.scalar(select(Group).where(Group.id == group_id).with_for_update())
    if group is None:
        raise HTTPException(404, "Group not found")
    code = secrets.token_urlsafe(12).upper()
    group.invite_hash = invite_hash(code)
    db.commit()
    return group_data(group, "admin", code)


@app.get("/groups/{group_id}/members")
def list_members(group_id: uuid.UUID, user: User = Depends(current_user), db: Session = Depends(get_db)) -> list[dict]:
    membership(db, group_id, user.id)
    rows = db.execute(select(User, Membership.role).join(Membership, Membership.user_id == User.id)
                      .where(Membership.group_id == group_id).order_by(User.username, User.id)).all()
    return [{"id": str(member.id), "username": member.username,
             "display_name": display_name(member), "role": role} for member, role in rows]


def get_duel(db: Session, duel_id: uuid.UUID, user_id: uuid.UUID, lock: bool = False) -> Duel:
    statement = select(Duel).where(Duel.id == duel_id)
    duel = db.scalar(statement.with_for_update() if lock else statement)
    if duel is None:
        raise HTTPException(404, "Duel not found")
    membership(db, duel.group_id, user_id)
    return duel


@app.post("/groups/{group_id}/duels", status_code=201)
def create_duel(group_id: uuid.UUID, body: CreateDuel, user: User = Depends(current_user),
                db: Session = Depends(get_db)) -> dict:
    membership(db, group_id, user.id, admin=True)
    if body.member_a_id == body.member_b_id:
        raise HTTPException(422, "Two distinct members required")
    membership(db, group_id, body.member_a_id)
    membership(db, group_id, body.member_b_id)
    deadline = body.deadline_at.astimezone(UTC)
    if not before_deadline(utc_now(), deadline):
        raise HTTPException(422, "Deadline must be in the future")
    duel = Duel(group_id=group_id, member_a_id=body.member_a_id, member_b_id=body.member_b_id,
                claim_type=body.claim_type, gameweek=body.gameweek.strip(), deadline_at=deadline)
    db.add(duel)
    db.commit()
    db.refresh(duel)
    return duel_data(db, duel, user.id)


def latest_submissions(db: Session, duel_id: uuid.UUID) -> dict[uuid.UUID, Submission]:
    rows = db.scalars(select(Submission).where(Submission.duel_id == duel_id)
                      .order_by(Submission.created_at.desc(), Submission.id.desc())).all()
    latest: dict[uuid.UUID, Submission] = {}
    for row in rows:
        latest.setdefault(row.user_id, row)
    return latest


def latest_revision(db: Session, duel_id: uuid.UUID) -> ScoreRevision | None:
    return db.scalar(select(ScoreRevision).where(ScoreRevision.duel_id == duel_id)
                     .order_by(ScoreRevision.created_at.desc(), ScoreRevision.id.desc()).limit(1))


def duel_data(db: Session, duel: Duel, viewer_id: uuid.UUID) -> dict:
    now = utc_now()
    submissions = latest_submissions(db, duel.id)
    revision = latest_revision(db, duel.id)
    notice = db.scalar(select(ScoreNotice).where(ScoreNotice.revision_id == revision.id)) if revision else None
    confirms = db.scalars(select(Confirmation).where(Confirmation.revision_id == revision.id)).all() if revision else []
    actions = {str(c.user_id): c.action for c in confirms}
    void = db.scalar(select(VoidEvent).where(VoidEvent.duel_id == duel.id))
    state = resolution_state(now, duel.deadline_at, duel.member_a_id in submissions,
                             duel.member_b_id in submissions,
                             (revision.score_a, revision.score_b) if revision else None,
                             notice.created_at if notice else None, actions, void is not None)
    revealed = not before_deadline(now, duel.deadline_at)
    probabilities = {str(user_id): row.probability_pct for user_id, row in submissions.items()
                     if revealed or user_id == viewer_id}
    revisions = db.scalars(select(ScoreRevision).where(ScoreRevision.duel_id == duel.id)
                           .order_by(ScoreRevision.created_at, ScoreRevision.id)).all()
    all_responses = db.scalars(select(Confirmation).where(
        Confirmation.revision_id.in_([r.id for r in revisions])
    )).all() if revisions else []
    return {
        "id": str(duel.id), "group_id": str(duel.group_id), "gameweek": duel.gameweek,
        "claim_type": duel.claim_type, "member_a_id": str(duel.member_a_id),
        "member_b_id": str(duel.member_b_id), "deadline_at": duel.deadline_at.isoformat(),
        "status": state, "probabilities": probabilities,
        "scores": [{"id": str(r.id), "score_a": r.score_a, "score_b": r.score_b,
                    "source_url": r.source_url, "created_at": r.created_at.isoformat(),
                    "entered_by": str(r.entered_by),
                    "responses": [{"user_id": str(c.user_id), "action": c.action, "reason": c.reason,
                                   "created_at": c.created_at.isoformat()} for c in all_responses
                                  if c.revision_id == r.id]} for r in revisions],
        "void_reason": void.reason if void else ("Missing submission" if state == "void" and not revision
                                                   else "Tie" if state == "void" else None),
    }


@app.get("/groups/{group_id}/duels")
def list_duels(group_id: uuid.UUID, user: User = Depends(current_user), db: Session = Depends(get_db)) -> list[dict]:
    membership(db, group_id, user.id)
    rows = db.scalars(select(Duel).where(Duel.group_id == group_id).order_by(Duel.created_at.desc())).all()
    return [duel_data(db, row, user.id) for row in rows]


@app.get("/duels/{duel_id}")
def read_duel(duel_id: uuid.UUID, user: User = Depends(current_user), db: Session = Depends(get_db)) -> dict:
    return duel_data(db, get_duel(db, duel_id, user.id), user.id)


@app.post("/duels/{duel_id}/submissions", status_code=201)
def submit_probability(duel_id: uuid.UUID, body: SubmitProbability,
                       user: User = Depends(current_user), db: Session = Depends(get_db)) -> dict:
    duel = get_duel(db, duel_id, user.id, lock=True)
    if user.id not in (duel.member_a_id, duel.member_b_id):
        raise HTTPException(403, "Only participants may submit")
    if not before_deadline(utc_now(), duel.deadline_at):
        raise HTTPException(409, "Deadline has passed")
    if not valid_probability(body.probability_pct):
        raise HTTPException(422, "Use a probability from 0 to 100 in steps of 5")
    if db.scalar(select(VoidEvent).where(VoidEvent.duel_id == duel.id)):
        raise HTTPException(409, "Duel is void")
    row = Submission(duel_id=duel.id, user_id=user.id, probability_pct=body.probability_pct)
    db.add(row)
    db.commit()
    return {"id": str(row.id), "probability_pct": row.probability_pct}


@app.post("/duels/{duel_id}/void")
def void_duel(duel_id: uuid.UUID, body: VoidDuel, user: User = Depends(current_user),
              db: Session = Depends(get_db)) -> dict:
    duel = get_duel(db, duel_id, user.id, lock=True)
    membership(db, duel.group_id, user.id, admin=True)
    if db.scalar(select(VoidEvent).where(VoidEvent.duel_id == duel.id)):
        raise HTTPException(409, "Already void")
    db.add(VoidEvent(duel_id=duel.id, entered_by=user.id, reason=body.reason.strip()))
    db.commit()
    return duel_data(db, duel, user.id)


@app.post("/duels/{duel_id}/scores", status_code=201)
def enter_scores(duel_id: uuid.UUID, body: EnterScore, user: User = Depends(current_user),
                 db: Session = Depends(get_db)) -> dict:
    duel = get_duel(db, duel_id, user.id, lock=True)
    membership(db, duel.group_id, user.id, admin=True)
    submissions = latest_submissions(db, duel.id)
    if before_deadline(utc_now(), duel.deadline_at) or not all(
        member_id in submissions for member_id in (duel.member_a_id, duel.member_b_id)
    ):
        raise HTTPException(409, "Scores require a closed duel with both submissions")
    if db.scalar(select(VoidEvent).where(VoidEvent.duel_id == duel.id)):
        raise HTTPException(409, "Duel is void")
    revision = ScoreRevision(duel_id=duel.id, entered_by=user.id, score_a=body.score_a,
                             score_b=body.score_b, source_url=str(body.source_url))
    db.add(revision)
    db.flush()
    if user.id in (duel.member_a_id, duel.member_b_id):
        db.add(Confirmation(revision_id=revision.id, user_id=user.id, action="confirm"))
    addresses = [db.get(User, member_id).email for member_id in (duel.member_a_id, duel.member_b_id)]
    try:
        send_score_notice(addresses, str(duel.id))
    except Exception as exc:
        db.rollback()
        raise HTTPException(503, "Score notice could not be delivered; retry") from exc
    db.add(ScoreNotice(revision_id=revision.id))
    db.commit()
    return duel_data(db, duel, user.id)


def respond_to_score(duel_id: uuid.UUID, revision_id: uuid.UUID, action: str, reason: str | None,
                     user: User, db: Session) -> dict:
    duel = get_duel(db, duel_id, user.id, lock=True)
    if user.id not in (duel.member_a_id, duel.member_b_id):
        raise HTTPException(403, "Only participants may respond")
    revision = latest_revision(db, duel.id)
    if revision is None or revision.id != revision_id:
        raise HTTPException(409, "Score revision is no longer current")
    if db.scalar(select(Confirmation).where(Confirmation.revision_id == revision.id,
                                            Confirmation.user_id == user.id)):
        raise HTTPException(409, "Already responded")
    current = duel_data(db, duel, user.id)
    if current["status"] not in ("awaiting_confirmation", "disputed"):
        raise HTTPException(409, "Confirmation window is closed")
    if action == "dispute":
        past = db.scalar(select(Confirmation).join(ScoreRevision, Confirmation.revision_id == ScoreRevision.id)
                         .where(ScoreRevision.duel_id == duel.id, Confirmation.user_id == user.id,
                                Confirmation.action == "dispute", ScoreRevision.score_a == revision.score_a,
                                ScoreRevision.score_b == revision.score_b))
        if past:
            raise HTTPException(409, "You already disputed these unchanged scores")
    db.add(Confirmation(revision_id=revision.id, user_id=user.id, action=action, reason=reason))
    db.commit()
    return duel_data(db, duel, user.id)


@app.post("/duels/{duel_id}/scores/{revision_id}/confirm")
def confirm_score(duel_id: uuid.UUID, revision_id: uuid.UUID,
                  user: User = Depends(current_user), db: Session = Depends(get_db)) -> dict:
    return respond_to_score(duel_id, revision_id, "confirm", None, user, db)


@app.post("/duels/{duel_id}/scores/{revision_id}/dispute")
def dispute_score(duel_id: uuid.UUID, revision_id: uuid.UUID, body: DisputeScore,
                  user: User = Depends(current_user), db: Session = Depends(get_db)) -> dict:
    return respond_to_score(duel_id, revision_id, "dispute", body.reason.strip(), user, db)


@app.get("/groups/{group_id}/history")
def history(group_id: uuid.UUID, user: User = Depends(current_user), db: Session = Depends(get_db)) -> dict:
    membership(db, group_id, user.id)
    members = list_members(group_id, user, db)
    duels = db.scalars(select(Duel).where(Duel.group_id == group_id)).all()
    records = {m["id"]: {"display_name": m["display_name"], "sample_size": 0,
                           "mean_brier": None, "wins": 0, "losses": 0, "history": []} for m in members}
    totals = {member_id: 0.0 for member_id in records}
    for duel in duels:
        detail = duel_data(db, duel, user.id)
        state = detail["status"]
        if state not in ("resolved", "void"):
            continue
        revision = latest_revision(db, duel.id)
        submissions = latest_submissions(db, duel.id) if state == "resolved" else {}
        for member_id, other_id, own_score, other_score in (
            (duel.member_a_id, duel.member_b_id, revision.score_a if revision else None,
             revision.score_b if revision else None),
            (duel.member_b_id, duel.member_a_id, revision.score_b if revision else None,
             revision.score_a if revision else None),
        ):
            record = records[str(member_id)]
            entry = {"duel_id": str(duel.id), "gameweek": duel.gameweek,
                     "claim_type": duel.claim_type, "opponent_id": str(other_id),
                     "status": state, "void_reason": detail["void_reason"]}
            if state == "resolved":
                probability = submissions[member_id].probability_pct
                score = brier(probability, own_score > other_score)
                entry.update({"probability_pct": probability, "won": own_score > other_score,
                              "brier": score})
                record["sample_size"] += 1
                record["wins" if own_score > other_score else "losses"] += 1
                totals[str(member_id)] += score
            record["history"].append(entry)
    for member_id, record in records.items():
        if record["sample_size"]:
            record["mean_brier"] = totals[member_id] / record["sample_size"]
    return records
