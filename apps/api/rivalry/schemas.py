import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, HttpUrl, field_validator


class CreateGroup(BaseModel):
    name: str = Field(min_length=2, max_length=80)


class JoinGroup(BaseModel):
    invite_code: str = Field(min_length=8, max_length=100)


class CreateDuel(BaseModel):
    member_a_id: uuid.UUID
    member_b_id: uuid.UUID
    claim_type: Literal["gameweek_points", "captain_points"]
    gameweek: str = Field(min_length=1, max_length=40)
    deadline_at: datetime

    @field_validator("deadline_at")
    @classmethod
    def timezone_required(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("Deadline must include a timezone")
        return value


class SubmitProbability(BaseModel):
    probability_pct: int


class EnterScore(BaseModel):
    score_a: int = Field(ge=0)
    score_b: int = Field(ge=0)
    source_url: HttpUrl

    @field_validator("source_url")
    @classmethod
    def official_source(cls, value: HttpUrl) -> HttpUrl:
        if value.host != "fantasy.premierleague.com":
            raise ValueError("Use an official Fantasy Premier League source link")
        return value


class DisputeScore(BaseModel):
    reason: str = Field(min_length=10, max_length=1000)


class VoidDuel(BaseModel):
    reason: str = Field(min_length=5, max_length=500)
