from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from sqlalchemy.orm import Session, joinedload
from backend.database import get_db
from backend.models import Tournament, TournamentPlayer, Match
from backend.services.leaderboard import compute_leaderboard
from backend.services.instagram import generate_story, FORMATS

router = APIRouter(prefix="/api/tournaments/{tid}/story", tags=["story"])


@router.get("")
def get_story(
    tid: int,
    fmt: str = Query("midnight", alias="format"),
    db: Session = Depends(get_db),
):
    t = db.get(Tournament, tid)
    if not t:
        raise HTTPException(404, "Tournament not found")
    if fmt not in FORMATS:
        raise HTTPException(400, f"Unknown format. Choose from: {', '.join(FORMATS)}")

    tps = (
        db.query(TournamentPlayer)
        .options(joinedload(TournamentPlayer.player))
        .filter(TournamentPlayer.tournament_id == tid)
        .all()
    )
    tp_list = [
        {"player_id": tp.player_id, "player_name": tp.player.name,
         "skill": tp.skill, "status": tp.status}
        for tp in tps
    ]
    finished = db.query(Match).filter(
        Match.tournament_id == tid, Match.status == "finished"
    ).all()
    match_list = [
        {"team_a": m.team_a, "team_b": m.team_b,
         "score_a": m.score_a, "score_b": m.score_b}
        for m in finished
    ]

    entries   = compute_leaderboard(tp_list, match_list)
    png_bytes = generate_story(t.name, entries, fmt=fmt)
    return Response(content=png_bytes, media_type="image/png")
