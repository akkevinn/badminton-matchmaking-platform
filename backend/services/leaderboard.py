"""
Leaderboard calculation.

Points = score earned in each match (0–30).
e.g. 21-15 result → Team A players each get 21 pts, Team B players each get 15 pts.
Ranking: total_points desc → wins desc → player name asc.
"""

from typing import List, Dict


def compute_leaderboard(
    tournament_players: List[Dict],
    finished_matches: List[Dict],
) -> List[Dict]:
    stats: Dict[int, Dict] = {}
    for tp in tournament_players:
        stats[tp["player_id"]] = {
            "player_id":       tp["player_id"],
            "player_name":     tp["player_name"],
            "skill":           tp["skill"],
            "games_played":    0,
            "wins":            0,
            "losses":          0,
            "points_scored":   0,
            "points_conceded": 0,
            "total_points":    0,
        }

    for m in finished_matches:
        sa, sb = m["score_a"], m["score_b"]
        winner = "a" if sa > sb else "b"

        for pid in m["team_a"]:
            if pid not in stats:
                continue
            stats[pid]["games_played"]    += 1
            stats[pid]["points_scored"]   += sa
            stats[pid]["points_conceded"] += sb
            stats[pid]["total_points"]    += sa
            if winner == "a":
                stats[pid]["wins"]  += 1
            else:
                stats[pid]["losses"] += 1

        for pid in m["team_b"]:
            if pid not in stats:
                continue
            stats[pid]["games_played"]    += 1
            stats[pid]["points_scored"]   += sb
            stats[pid]["points_conceded"] += sa
            stats[pid]["total_points"]    += sb
            if winner == "b":
                stats[pid]["wins"]  += 1
            else:
                stats[pid]["losses"] += 1

    entries = sorted(
        stats.values(),
        key=lambda x: (-x["total_points"], -x["wins"], x["player_name"]),
    )
    for i, e in enumerate(entries):
        e["rank"] = i + 1

    return entries
