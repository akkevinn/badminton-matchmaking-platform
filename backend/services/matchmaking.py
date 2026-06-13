"""
Matchmaking service.

Courts advance independently: a match is generated for whichever court is
free, drawn from the players who are not currently playing on another court.

Rules (in priority order):
1. Availability: only players not already in a live match are eligible
   (the caller filters these out before calling pick_matches).
2. Fairness: the players with the fewest games played play next. Players
   who just finished have a higher count, so they yield to rested players.
3. No repeated teammate pair from recent matches (heavy penalty — avoided
   unless every split repeats a pair).
4. Skill balance: among the 3 possible team splits for the chosen 4
   players, pick the split with the lowest absolute skill difference.
"""

import math
import random
from typing import List, Tuple, Dict, Set, FrozenSet


def pick_matches(
    available_players: List[Dict],
    num_to_fill: int,
    recent_pairs: Set[FrozenSet] = None,
) -> List[Tuple[List[int], List[int]]]:
    """
    Fill up to `num_to_fill` courts from the available player pool.

    Courts advance independently, so this works on whoever is free right
    now rather than a synchronised round.

    Parameters
    ----------
    available_players : list of player dicts — active players who are NOT
        currently in a pending/ongoing match. Required keys: id, skill,
        games_played.
    num_to_fill : how many courts to fill this call (>=1)
    recent_pairs : set of frozenset({id1, id2}) — recent teammate pairs to
        avoid repeating. Pass set() or omit to skip.

    Returns
    -------
    list of (team_a_ids, team_b_ids) — one tuple per court filled, using
    non-overlapping players.
    """
    if recent_pairs is None:
        recent_pairs = set()

    eligible = list(available_players)
    if len(eligible) < 4 or num_to_fill < 1:
        return []

    # Shuffle first so equal-priority players rotate randomly.
    # Python's sort is stable, so the shuffle order is preserved within
    # tied game-count groups — this is what mixes up pairings over time.
    random.shuffle(eligible)

    # Fairness: fewest games played first. Players who just finished a game
    # have a higher count, so they naturally yield to rested players.
    eligible.sort(key=lambda p: p["games_played"])

    matches  = []
    used_ids: set = set()
    courts_to_fill = min(num_to_fill, len(eligible) // 4)

    for _ in range(courts_to_fill):
        candidates = [p for p in eligible if p["id"] not in used_ids]
        if len(candidates) < 4:
            break

        # ── Always pick the 4 least-played available players ─────────────────
        four = candidates[:4]

        # ── Rules 2 & 4: find the best team split ────────────────────────────
        SPLITS = (
            ((0, 1), (2, 3)),
            ((0, 2), (1, 3)),
            ((0, 3), (1, 2)),
        )

        best_match = None
        best_score = math.inf

        for ai, bi in SPLITS:
            ta = [four[i] for i in ai]
            tb = [four[i] for i in bi]

            skill_diff = abs(
                sum(p["skill"] for p in ta) - sum(p["skill"] for p in tb)
            )

            # Penalise repeated teammate pairs from recent matches
            # (weight 1000 >> any skill_diff, so it's effectively a hard
            # constraint — but falls back to best skill balance if all
            # three splits repeat a pair)
            repeated = sum(
                1 for pair in (
                    frozenset({ta[0]["id"], ta[1]["id"]}),
                    frozenset({tb[0]["id"], tb[1]["id"]}),
                )
                if pair in recent_pairs
            )

            score = repeated * 1000 + skill_diff
            if score < best_score:
                best_score = score
                best_match = (ta, tb)

        if best_match:
            ta, tb = best_match
            matches.append(([p["id"] for p in ta], [p["id"] for p in tb]))
            for p in ta + tb:
                used_ids.add(p["id"])

    return matches
