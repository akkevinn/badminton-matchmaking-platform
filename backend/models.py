from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from backend.database import Base


class Player(Base):
    __tablename__ = "players"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    default_skill = Column(Float, default=5.0)
    created_at = Column(DateTime, server_default=func.now())

    tournament_entries = relationship("TournamentPlayer", back_populates="player")


class Tournament(Base):
    __tablename__ = "tournaments"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    num_courts = Column(Integer, default=1)
    max_points = Column(Integer, default=21)
    deuce_enabled = Column(Boolean, default=True)
    status = Column(String, default="active")  # active | finished
    created_at = Column(DateTime, server_default=func.now())
    finished_at = Column(DateTime, nullable=True)

    players = relationship("TournamentPlayer", back_populates="tournament")
    matches = relationship("Match", back_populates="tournament")


class TournamentPlayer(Base):
    __tablename__ = "tournament_players"

    id = Column(Integer, primary_key=True, index=True)
    tournament_id = Column(Integer, ForeignKey("tournaments.id"), nullable=False)
    player_id = Column(Integer, ForeignKey("players.id"), nullable=False)
    skill = Column(Float, nullable=False)
    status = Column(String, default="active")  # active | away | left
    joined_at = Column(DateTime, server_default=func.now())
    left_at = Column(DateTime, nullable=True)

    tournament = relationship("Tournament", back_populates="players")
    player = relationship("Player", back_populates="tournament_entries")


class Match(Base):
    __tablename__ = "matches"

    id = Column(Integer, primary_key=True, index=True)
    tournament_id = Column(Integer, ForeignKey("tournaments.id"), nullable=False)
    court = Column(Integer, nullable=False)
    round_number = Column(Integer, nullable=False)
    # JSON arrays of player_ids: [p1, p2] vs [p3, p4]
    team_a = Column(JSON, nullable=False)
    team_b = Column(JSON, nullable=False)
    score_a = Column(Integer, nullable=True)
    score_b = Column(Integer, nullable=True)
    status = Column(String, default="pending")  # pending | ongoing | finished
    created_at = Column(DateTime, server_default=func.now())
    finished_at = Column(DateTime, nullable=True)

    tournament = relationship("Tournament", back_populates="matches")
