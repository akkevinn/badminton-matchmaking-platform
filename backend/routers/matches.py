from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from backend.database import get_db
from backend.models import Match, Tournament, TournamentPlayer
from backend.schemas import MatchScoreUpdate, MatchOut
from backend.services.matchmaking import generate_round
from backend.services.leaderboard import compute_leaderboard
from typing import List
from datetime import datetime, timezone

router = APIRouter(prefix="/api/tournaments/{tid}/matches", tags=["matches"])


def _get_tournament(tid: int, db: Session) -> Tournament:
    t = db.get(Tournament, tid)
    if not t:
        raise HTTPException(404, "Tournament not found")
    return t


def _player_stats(tid: int, db: Session) -> dict:
    """Returns {player_id: {games_played, last_match_round, second_last_match_round}} for active players."""
    tps = (
        db.query(TournamentPlayer)
        .filter(TournamentPlayer.tournament_id == tid, TournamentPlayer.status == "active")
        .all()
    )
    stats = {
        tp.player_id: {
            "id": tp.player_id,
            "skill": tp.skill,
            "games_played": 0,
            "last_match_round": None,
            "second_last_match_round": None,
        }
        for tp in tps
    }

    finished = (
        db.query(Match)
        .filter(Match.tournament_id == tid, Match.status == "finished")
        .all()
    )

    # Collect every round each player has appeared in, then derive last two
    rounds_by_player: dict = {pid: [] for pid in stats}
    for m in finished:
        for pid in (m.team_a or []) + (m.team_b or []):
            if pid in stats:
                stats[pid]["games_played"] += 1
                rounds_by_player[pid].append(m.round_number)

    for pid, rounds in rounds_by_player.items():
        if rounds:
            sorted_rounds = sorted(set(rounds), reverse=True)  # unique, most-recent first
            stats[pid]["last_match_round"] = sorted_rounds[0]
            stats[pid]["second_last_match_round"] = sorted_rounds[1] if len(sorted_rounds) >= 2 else None

    return stats


@router.get("", response_model=List[MatchOut])
def list_matches(tid: int, db: Session = Depends(get_db)):
    _get_tournament(tid, db)
    return db.query(Match).filter(Match.tournament_id == tid).order_by(Match.round_number, Match.court).all()


@router.post("/generate", status_code=201)
def generate_matches(tid: int, db: Session = Depends(get_db)):
    t = _get_tournament(tid, db)
    if t.status == "finished":
        raise HTTPException(400, "Tournament is finished")

    # Check no ongoing matches exist
    ongoing = db.query(Match).filter(Match.tournament_id == tid, Match.status.in_(["pending", "ongoing"])).count()
    if ongoing > 0:
        raise HTTPException(400, "Finish or cancel existing matches before generating new ones")

    stats = _player_stats(tid, db)
    if len(stats) < 4:
        raise HTTPException(400, "Need at least 4 active players to generate matches")

    last_round = db.query(Match).filter(Match.tournament_id == tid).order_by(Match.round_number.desc()).first()
    current_round = (last_round.round_number + 1) if last_round else 1

    # Build teammate-pair set from the most recent round to avoid
    # scheduling the same pair as teammates in back-to-back rounds.
    last_round_pairs: set = set()
    if last_round:
        prev_matches = (
            db.query(Match)
            .filter(Match.tournament_id == tid, Match.round_number == last_round.round_number)
            .all()
        )
        for m in prev_matches:
            a = m.team_a or []
            b = m.team_b or []
            if len(a) == 2:
                last_round_pairs.add(frozenset(a))
            if len(b) == 2:
                last_round_pairs.add(frozenset(b))

    players_list = list(stats.values())
    court_matches = generate_round(players_list, t.num_courts, current_round, last_round_pairs)

    if not court_matches:
        raise HTTPException(400, "Not enough eligible players to form matches")

    created = []
    for court_idx, (team_a, team_b) in enumerate(court_matches, start=1):
        m = Match(
            tournament_id=tid,
            court=court_idx,
            round_number=current_round,
            team_a=team_a,
            team_b=team_b,
            status="pending",
        )
        db.add(m)
        created.append(m)

    db.commit()
    for m in created:
        db.refresh(m)
    return created


@router.patch("/{match_id}/start", response_model=MatchOut)
def start_match(tid: int, match_id: int, db: Session = Depends(get_db)):
    m = db.query(Match).filter(Match.id == match_id, Match.tournament_id == tid).first()
    if not m:
        raise HTTPException(404, "Match not found")
    if m.status != "pending":
        raise HTTPException(400, "Match is not in pending state")
    m.status = "ongoing"
    db.commit()
    db.refresh(m)
    return m


@router.patch("/{match_id}/score", response_model=MatchOut)
def update_score(tid: int, match_id: int, data: MatchScoreUpdate, db: Session = Depends(get_db)):
    t = _get_tournament(tid, db)
    m = db.query(Match).filter(Match.id == match_id, Match.tournament_id == tid).first()
    if not m:
        raise HTTPException(404, "Match not found")
    if m.status == "finished":
        raise HTTPException(400, "Match already finished")
    if m.status != "ongoing":
        raise HTTPException(400, "Start the match before entering a score")

    sa, sb = data.score_a, data.score_b
    max_pts = t.max_points

    # Validate deuce logic
    if t.deuce_enabled:
        cap = max_pts + 9  # BWF deuce cap: 30 for 21-pt game
        if sa > cap or sb > cap:
            raise HTTPException(400, f"Score cannot exceed {cap} with deuce enabled")
        if sa >= max_pts or sb >= max_pts:
            # One side reached max: must be ahead by 2 unless at cap
            winner_score = max(sa, sb)
            loser_score = min(sa, sb)
            if winner_score < cap and (winner_score - loser_score) < 2:
                raise HTTPException(400, "Deuce: winning team must be ahead by at least 2 points")
    else:
        if sa > max_pts or sb > max_pts:
            raise HTTPException(400, f"Score cannot exceed {max_pts}")

    m.score_a = sa
    m.score_b = sb
    db.commit()
    db.refresh(m)
    return m


@router.patch("/{match_id}/finish", response_model=MatchOut)
def finish_match(tid: int, match_id: int, db: Session = Depends(get_db)):
    m = db.query(Match).filter(Match.id == match_id, Match.tournament_id == tid).first()
    if not m:
        raise HTTPException(404, "Match not found")
    if m.status == "finished":
        raise HTTPException(400, "Match already finished")
    if m.score_a is None or m.score_b is None:
        raise HTTPException(400, "Set the score before finishing")
    if m.score_a == m.score_b:
        raise HTTPException(400, "A match cannot end in a draw")
    m.status = "finished"
    m.finished_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(m)
    return m


@router.patch("/{match_id}/teams", response_model=MatchOut)
def edit_match_teams(
    tid: int, match_id: int,
    team_a: str, team_b: str,   # comma-separated player ids e.g. "1,2" and "3,4"
    db: Session = Depends(get_db),
):
    """
    Freely reassign all 4 players in a match.
    Accepts team_a and team_b as comma-separated player id strings.
    Players can be swapped within the same match (partner switch) or
    replaced with any active tournament player.
    """
    m = db.query(Match).filter(Match.id == match_id, Match.tournament_id == tid).first()
    if not m:
        raise HTTPException(404, "Match not found")
    if m.status == "finished":
        raise HTTPException(400, "Cannot edit a finished match")

    try:
        new_a = [int(x.strip()) for x in team_a.split(",")]
        new_b = [int(x.strip()) for x in team_b.split(",")]
    except ValueError:
        raise HTTPException(400, "Invalid player ids")

    if len(new_a) != 2 or len(new_b) != 2:
        raise HTTPException(400, "Each team must have exactly 2 players")

    all_ids = new_a + new_b
    if len(set(all_ids)) != 4:
        raise HTTPException(400, "All 4 players must be different")

    # Verify every player is active in this tournament
    active_ids = {
        tp.player_id for tp in
        db.query(TournamentPlayer).filter(
            TournamentPlayer.tournament_id == tid,
            TournamentPlayer.status == "active",
        ).all()
    }
    for pid in all_ids:
        if pid not in active_ids:
            raise HTTPException(400, f"Player {pid} is not active in this tournament")

    m.team_a = new_a
    m.team_b = new_b
    db.commit()
    db.refresh(m)
    return m


@router.get("/leaderboard")
def get_leaderboard(tid: int, db: Session = Depends(get_db)):
    _get_tournament(tid, db)
    tps = (
        db.query(TournamentPlayer)
        .options(joinedload(TournamentPlayer.player))
        .filter(TournamentPlayer.tournament_id == tid)
        .all()
    )
    tp_list = [{"player_id": tp.player_id, "player_name": tp.player.name, "skill": tp.skill, "status": tp.status} for tp in tps]

    finished = db.query(Match).filter(Match.tournament_id == tid, Match.status == "finished").all()
    match_list = [{"team_a": m.team_a, "team_b": m.team_b, "score_a": m.score_a, "score_b": m.score_b} for m in finished]

    return compute_leaderboard(tp_list, match_list)
