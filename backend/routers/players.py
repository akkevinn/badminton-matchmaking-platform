from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.models import Player
from backend.schemas import PlayerCreate, PlayerUpdate, PlayerOut
from typing import List

router = APIRouter(prefix="/api/players", tags=["players"])


@router.get("", response_model=List[PlayerOut])
def list_players(db: Session = Depends(get_db)):
    return db.query(Player).order_by(Player.name).all()


@router.post("", response_model=PlayerOut, status_code=201)
def create_player(data: PlayerCreate, db: Session = Depends(get_db)):
    if db.query(Player).filter(Player.name == data.name).first():
        raise HTTPException(400, "Player name already exists")
    player = Player(**data.model_dump())
    db.add(player)
    db.commit()
    db.refresh(player)
    return player


@router.get("/{player_id}", response_model=PlayerOut)
def get_player(player_id: int, db: Session = Depends(get_db)):
    player = db.get(Player, player_id)
    if not player:
        raise HTTPException(404, "Player not found")
    return player


@router.patch("/{player_id}", response_model=PlayerOut)
def update_player(player_id: int, data: PlayerUpdate, db: Session = Depends(get_db)):
    player = db.get(Player, player_id)
    if not player:
        raise HTTPException(404, "Player not found")
    for k, v in data.model_dump(exclude_none=True).items():
        setattr(player, k, v)
    db.commit()
    db.refresh(player)
    return player


@router.delete("/{player_id}", status_code=204)
def delete_player(player_id: int, db: Session = Depends(get_db)):
    player = db.get(Player, player_id)
    if not player:
        raise HTTPException(404, "Player not found")
    db.delete(player)
    db.commit()
