from pydantic import BaseModel, Field
from typing import Optional, List, Literal
from datetime import datetime


# Player
class PlayerCreate(BaseModel):
    name: str
    default_skill: float = Field(5.0, ge=1, le=10)


class PlayerUpdate(BaseModel):
    name: Optional[str] = None
    default_skill: Optional[float] = Field(None, ge=1, le=10)


class PlayerOut(BaseModel):
    id: int
    name: str
    default_skill: float
    created_at: datetime

    model_config = {"from_attributes": True}


# Tournament
class TournamentCreate(BaseModel):
    name: str
    sport: Literal["badminton", "padel"] = "badminton"
    num_courts: int = Field(1, ge=1, le=4)
    max_points: int = Field(21, ge=11)
    deuce_enabled: bool = True


class TournamentUpdate(BaseModel):
    name: Optional[str] = None
    num_courts: Optional[int] = Field(None, ge=1, le=4)
    max_points: Optional[int] = Field(None, ge=11)
    deuce_enabled: Optional[bool] = None


class TournamentOut(BaseModel):
    id: int
    name: str
    sport: str
    num_courts: int
    max_points: int
    deuce_enabled: bool
    status: str
    created_at: datetime
    finished_at: Optional[datetime]

    model_config = {"from_attributes": True}


# Tournament Player
class TournamentPlayerAdd(BaseModel):
    player_id: int
    skill: float = Field(..., ge=1, le=10)


class TournamentPlayerUpdate(BaseModel):
    skill: Optional[float] = Field(None, ge=1, le=10)
    status: Optional[str] = None  # active | away | left


class TournamentPlayerOut(BaseModel):
    id: int
    tournament_id: int
    player_id: int
    player_name: str
    skill: float
    status: str
    joined_at: datetime
    left_at: Optional[datetime]

    model_config = {"from_attributes": True}


# Match
class MatchScoreUpdate(BaseModel):
    score_a: int = Field(..., ge=0)
    score_b: int = Field(..., ge=0)


class MatchOut(BaseModel):
    id: int
    tournament_id: int
    court: int
    round_number: int
    team_a: List[int]
    team_b: List[int]
    score_a: Optional[int]
    score_b: Optional[int]
    status: str
    created_at: datetime
    finished_at: Optional[datetime]

    model_config = {"from_attributes": True}


# Leaderboard
class LeaderboardEntry(BaseModel):
    player_id: int
    player_name: str
    skill: float
    games_played: int
    wins: int
    losses: int
    points_scored: int
    points_conceded: int
    total_points: int
    rank: int
