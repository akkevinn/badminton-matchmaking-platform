"""
Matchmaking service.

Rules (in priority order):
1. Hard rest: a player may NOT play three consecutive rounds.
   Relaxed only when fewer than 4 eligible players remain.
2. No repeated teammate pair in back-to-back rounds.
   (heavy penalty — avoided unless every split has a repeated pair)
3. Fairness: the 4 players with the fewest games always play next.
   Players with more games only fill a slot when not enough low-game
   players are available.
4. Skill balance: among the 3 possible team splits for those 4 players,
   pick the split with the lowest absolute skill difference.
5. Two consecutive rounds for a player are allowed; the rest-aware sort
   naturally rotates them when games counts are equal.
"""

import math
import random
from typing import List, Tuple, Dict, Set, FrozenSet


def generate_round(
    active_players: List[Dict],
    num_courts: int,
    current_round: int,
    last_round_pairs: Set[FrozenSet] = None,
) -> List[Tuple[List[int], List[int]]]:
    """
    Build one round of matches.

    Parameters
    ----------
    active_players : list of player dicts, all with status='active'
        Required keys: id, skill, games_played, last_match_round,
        second_last_match_round
    num_courts : how many simultaneous courts
    current_round : 1-based round number being generated
    last_round_pairs : set of frozenset({id1, id2}) — teammate pairs
        from the immediately preceding round.  Pass set() or omit for
        the first round.

    Returns
    -------
    list of (team_a_ids, team_b_ids) — one tuple per court filled.
    """
    if last_round_pairs is None:
        last_round_pairs = set()

    if len(active_players) < 4:
        return []

    # ── Rule 1: hard rest — exclude anyone who played both preceding rounds ──
    must_rest = {
        p["id"] for p in active_players
        if p.get("last_match_round") == current_round - 1
        and p.get("second_last_match_round") == current_round - 2
    }
    eligible = [p for p in active_players if p["id"] not in must_rest]
    if len(eligible) < 4:
        eligible = list(active_players)          # relax when pool is too small

    # Shuffle first so equal-priority players rotate randomly.
    # Python's sort is stable, so the shuffle order is preserved within
    # tied game-count groups — this is what mixes up pairings across rounds.
    random.shuffle(eligible)

    # Sort by fewest games only; tie-breaking is already randomised by the
    # shuffle above.  A rest-based secondary key would re-introduce the
    # deterministic group-alternation that makes rounds repeat.
    eligible.sort(key=lambda p: p["games_played"])

    matches  = []
    used_ids: set = set()
    courts_to_fill = min(num_courts, len(eligible) // 4)

    for _ in range(courts_to_fill):
        candidates = [p for p in eligible if p["id"] not in used_ids]
        if len(candidates) < 4:
            break

        # ── Rule 3: always pick the 4 least-played available players ─────────
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

            # Rule 2: penalise repeated teammate pairs from last round
            # (weight 1000 >> any skill_diff, so it's effectively a hard
            # constraint — but falls back to best skill balance if all
            # three splits repeat a pair)
            repeated = sum(
                1 for pair in (
                    frozenset({ta[0]["id"], ta[1]["id"]}),
                    frozenset({tb[0]["id"], tb[1]["id"]}),
                )
                if pair in last_round_pairs
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
