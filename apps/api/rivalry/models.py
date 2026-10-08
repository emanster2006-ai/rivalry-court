import uuid
from datetime import UTC, datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from rivalry.db import Base


def uuid_col() -> Mapped[uuid.UUID]:
    return mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)


class User(Base):
    __tablename__ = "users"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    email: Mapped[str] = mapped_column(String(320), unique=True)


class Group(Base):
    __tablename__ = "groups"
    id: Mapped[uuid.UUID] = uuid_col()
    name: Mapped[str] = mapped_column(String(80))
    invite_hash: Mapped[str] = mapped_column(String(64), unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), server_default=func.now())


class Membership(Base):
    __tablename__ = "memberships"
    __table_args__ = (UniqueConstraint("group_id", "user_id"),)
    id: Mapped[uuid.UUID] = uuid_col()
    group_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("groups.id"))
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    role: Mapped[str] = mapped_column(String(16))


class Duel(Base):
    __tablename__ = "duels"
    __table_args__ = (
        CheckConstraint("member_a_id <> member_b_id", name="different_members"),
        CheckConstraint("claim_type IN ('gameweek_points', 'captain_points')", name="claim_type"),
    )
    id: Mapped[uuid.UUID] = uuid_col()
    group_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("groups.id"))
    member_a_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    member_b_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    claim_type: Mapped[str] = mapped_column(String(32))
    gameweek: Mapped[str] = mapped_column(String(40))
    deadline_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), server_default=func.now())


class Submission(Base):
    __tablename__ = "submissions"
    __table_args__ = (
        CheckConstraint("probability_pct BETWEEN 0 AND 100 AND probability_pct % 5 = 0", name="probability_step"),
    )
    id: Mapped[uuid.UUID] = uuid_col()
    duel_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("duels.id"))
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    probability_pct: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), server_default=func.now())


class ScoreRevision(Base):
    __tablename__ = "score_revisions"
    __table_args__ = (CheckConstraint("score_a >= 0 AND score_b >= 0", name="nonnegative_scores"),)
    id: Mapped[uuid.UUID] = uuid_col()
    duel_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("duels.id"))
    entered_by: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    score_a: Mapped[int] = mapped_column(Integer)
    score_b: Mapped[int] = mapped_column(Integer)
    source_url: Mapped[str] = mapped_column(String(2048))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), server_default=func.now())


class ScoreNotice(Base):
    __tablename__ = "score_notices"
    __table_args__ = (UniqueConstraint("revision_id"),)
    id: Mapped[uuid.UUID] = uuid_col()
    revision_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("score_revisions.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), server_default=func.now())


class Confirmation(Base):
    __tablename__ = "confirmations"
    __table_args__ = (
        UniqueConstraint("revision_id", "user_id"),
        CheckConstraint("action IN ('confirm', 'dispute')", name="confirmation_action"),
    )
    id: Mapped[uuid.UUID] = uuid_col()
    revision_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("score_revisions.id"))
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    action: Mapped[str] = mapped_column(String(16))
    reason: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), server_default=func.now())


class VoidEvent(Base):
    __tablename__ = "void_events"
    __table_args__ = (UniqueConstraint("duel_id"),)
    id: Mapped[uuid.UUID] = uuid_col()
    duel_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("duels.id"))
    entered_by: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    reason: Mapped[str] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), server_default=func.now())
