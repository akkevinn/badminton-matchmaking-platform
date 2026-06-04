from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func
from backend.database import get_db
from backend.models import Tournament, TournamentPlayer, Player, Match
from backend.schemas import (
    TournamentCreate, TournamentUpdate, TournamentOut,
    TournamentPlayerAdd, TournamentPlayerUpdate, TournamentPlayerOut,
)
from typing import List
from datetime import datetime, timezone

router = APIRouter(prefix="/api/tournaments", tags=["tournaments"])


def _tp_out(tp: TournamentPlayer) -> dict:
    return {
        "id": tp.id,
        "tournament_id": tp.tournament_id,
        "player_id": tp.player_id,
        "player_name": tp.player.name,
        "skill": tp.skill,
        "status": tp.status,
        "joined_at": tp.joined_at,
        "left_at": tp.left_at,
    }


@router.get("", response_model=List[TournamentOut])
def list_tournaments(db: Session = Depends(get_db)):
    return db.query(Tournament).order_by(Tournament.created_at.desc()).all()


@router.post("", response_model=TournamentOut, status_code=201)
def create_tournament(data: TournamentCreate, db: Session = Depends(get_db)):
    t = Tournament(**data.model_dump())
    db.add(t)
    db.commit()
    db.refresh(t)
    return t


@router.get("/{tid}", response_model=TournamentOut)
def get_tournament(tid: int, db: Session = Depends(get_db)):
    t = db.get(Tournament, tid)
    if not t:
        raise HTTPException(404, "Tournament not found")
    return t


@router.patch("/{tid}", response_model=TournamentOut)
def update_tournament(tid: int, data: TournamentUpdate, db: Session = Depends(get_db)):
    t = db.get(Tournament, tid)
    if not t:
        raise HTTPException(404, "Tournament not found")
    if t.status == "finished":
        raise HTTPException(400, "Cannot edit a finished tournament")
    for k, v in data.model_dump(exclude_none=True).items():
        setattr(t, k, v)
    db.commit()
    db.refresh(t)
    return t


@router.delete("/{tid}", status_code=204)
def delete_tournament(tid: int, db: Session = Depends(get_db)):
    t = db.get(Tournament, tid)
    if not t:
        raise HTTPException(404, "Tournament not found")
    # Cascade-delete related records manually (SQLite doesn't enforce FK cascades by default)
    db.query(Match).filter(Match.tournament_id == tid).delete()
    db.query(TournamentPlayer).filter(TournamentPlayer.tournament_id == tid).delete()
    db.delete(t)
    db.commit()


# --- Players in tournament ---

@router.get("/{tid}/players")
def list_tournament_players(tid: int, db: Session = Depends(get_db)):
    tps = (
        db.query(TournamentPlayer)
        .options(joinedload(TournamentPlayer.player))
        .filter(TournamentPlayer.tournament_id == tid)
        .all()
    )
    return [_tp_out(tp) for tp in tps]


@router.post("/{tid}/players", status_code=201)
def add_player_to_tournament(tid: int, data: TournamentPlayerAdd, db: Session = Depends(get_db)):
    t = db.get(Tournament, tid)
    if not t:
        raise HTTPException(404, "Tournament not found")
    if t.status == "finished":
        raise HTTPException(400, "Tournament is finished")

    player = db.get(Player, data.player_id)
    if not player:
        raise HTTPException(404, "Player not found")

    existing = (
        db.query(TournamentPlayer)
        .filter(
            TournamentPlayer.tournament_id == tid,
            TournamentPlayer.player_id == data.player_id,
            TournamentPlayer.status != "left",
        )
        .first()
    )
    if existing:
        raise HTTPException(400, "Player already in tournament")

    tp = TournamentPlayer(tournament_id=tid, player_id=data.player_id, skill=data.skill)
    db.add(tp)

    # Update player's default skill
    player.default_skill = data.skill
    db.commit()
    db.refresh(tp)
    return _tp_out(tp)


@router.patch("/{tid}/players/{tp_id}")
def update_tournament_player(
    tid: int, tp_id: int, data: TournamentPlayerUpdate, db: Session = Depends(get_db)
):
    tp = db.query(TournamentPlayer).filter(
        TournamentPlayer.id == tp_id,
        TournamentPlayer.tournament_id == tid,
    ).first()
    if not tp:
        raise HTTPException(404, "Tournament player not found")

    if data.skill is not None:
        tp.skill = data.skill
        tp.player.default_skill = data.skill
    if data.status is not None:
        tp.status = data.status
        if data.status == "left":
            tp.left_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(tp)
    return _tp_out(tp)


# --- Finish tournament ---

@router.post("/{tid}/finish", response_model=TournamentOut)
def finish_tournament(tid: int, db: Session = Depends(get_db)):
    t = db.get(Tournament, tid)
    if not t:
        raise HTTPException(404, "Tournament not found")
    if t.status == "finished":
        raise HTTPException(400, "Already finished")
    t.status = "finished"
    t.finished_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(t)
    return t
