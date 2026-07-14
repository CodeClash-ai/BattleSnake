"""
Battlesnake bot for CodeClash.

Strategy overview:
  1. Compute the set of "safe" moves from the current head position:
     - stay in bounds
     - don't collide with any snake body (accounting for tails that will
       move away next turn unless that snake just ate food this turn, in
       which case its tail stays put)
     - avoid moving head-to-head into an equal-or-longer opposing snake
  2. Among safe moves, use flood-fill (BFS) to estimate the amount of open
     space reachable after each candidate move. Heavily penalize moves that
     lead into small/trapped pockets (less than our own body length) since
     that usually means death a few turns later.
  3. Score each safe move combining:
     - reachable space (avoid getting trapped)
     - distance to nearest food (prefer closer food, weighted by our health
       - low health means food is more urgent)
     - a bonus for moves that could set up a favorable head-to-head
       (moving toward a strictly shorter snake's head region is fine, but we
       never deliberately move adjacent to a longer snake's head)
     - a small centrality bonus to avoid hugging walls/corners early on
  4. If no safe moves exist (we're doomed), fall back to the move that
     maximizes flood-fill space, ignoring snake-collision safety, as a last
     resort (better than an immediate certain-death direction if there's any
     difference at all).
"""

import random

DIRS = {
    "up": (0, 1),
    "down": (0, -1),
    "left": (-1, 0),
    "right": (1, 0),
}


def info():
    return {
        "apiversion": "1",
        "author": "me",
        "color": "#ff00ff",
        "head": "beluga",
        "tail": "bolt",
    }


def start(game_state):
    return None


def end(game_state):
    return None


def _manhattan(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def _in_bounds(pt, width, height):
    return 0 <= pt[0] < width and 0 <= pt[1] < height


def _occupied_cells(board, you_id):
    """Return dict cell -> info about occupancy for collision checks.

    We build:
      blocked: set of cells that are always unsafe to move into (bodies
               excluding tails that will vacate)
      snake_lengths: dict id -> length
      heads: dict id -> (x,y)
    """
    blocked = set()
    tails_that_move = set()
    heads = {}
    lengths = {}
    tails = {}
    for snake in board["snakes"]:
        body = snake["body"]
        lengths[snake["id"]] = len(body)
        heads[snake["id"]] = (body[0]["x"], body[0]["y"])
        tails[snake["id"]] = (body[-1]["x"], body[-1]["y"])
        # Determine if this snake ate food last turn (tail didn't move).
        # Heuristic: if last two body segments are identical (stacked),
        # that indicates growth just happened (common battlesnake engine
        # behavior for the turn right after eating).
        ate_last_turn = False
        if len(body) >= 2:
            last = body[-1]
            second_last = body[-2]
            if last["x"] == second_last["x"] and last["y"] == second_last["y"]:
                ate_last_turn = True

        for i, seg in enumerate(body):
            cell = (seg["x"], seg["y"])
            is_tail = i == len(body) - 1
            if is_tail and not ate_last_turn:
                # tail will move away next turn -> safe-ish, don't block
                tails_that_move.add(cell)
            else:
                blocked.add(cell)

    # Remove tail cells from blocked only if they aren't also occupied by
    # another body segment (defensive; sets already prevent duplicates from
    # counting twice but overlapping snakes could still be an issue).
    return blocked, heads, lengths, tails


def _flood_fill(start, blocked, width, height, cap=None, target=None):
    """BFS from `start` over non-blocked in-bounds cells.

    Returns (count, reached_target):
      count -- number of reachable cells (including start), capped at `cap`
               if given (stops early once cap cells are found -- used only
               as a cheap early-exit; pass cap=None / a big number for a
               full/uncapped flood-fill, which is fine on small boards).
      reached_target -- True if `target` cell (e.g. our own tail) was seen
               during the search (useful to check "can I still get back to
               my tail" as a proxy for not being self-trapped later).
    """
    if start in blocked:
        return 0, (target == start)
    if cap is None:
        cap = width * height + 1
    seen = {start}
    frontier = [start]
    count = 1
    reached_target = start == target
    while frontier and count < cap:
        nxt = []
        for cell in frontier:
            for dx, dy in DIRS.values():
                npt = (cell[0] + dx, cell[1] + dy)
                if npt in seen:
                    continue
                if not _in_bounds(npt, width, height):
                    continue
                if npt in blocked:
                    continue
                seen.add(npt)
                count += 1
                if npt == target:
                    reached_target = True
                nxt.append(npt)
                if count >= cap:
                    break
            if count >= cap:
                break
        frontier = nxt
    return count, reached_target


def _flood_fill_size(start, blocked, width, height, cap):
    """Back-compat wrapper: just the count, capped."""
    count, _ = _flood_fill(start, blocked, width, height, cap=cap)
    return count


def _opp_candidate_cells(body, blocked, width, height):
    """Approximate legal next-head cells for an opposing snake.

    Uses the same global `blocked` set (bodies incl. tail-vacate logic) as
    a conservative proxy for what cells that snake could legally move into
    next turn. Doesn't know their actual strategy, just their physically
    legal moves.
    """
    head = (body[0]["x"], body[0]["y"])
    cells = []
    for dx, dy in DIRS.values():
        npt = (head[0] + dx, head[1] + dy)
        if _in_bounds(npt, width, height) and npt not in blocked:
            cells.append(npt)
    return cells


def move(game_state):
    try:
        board = game_state["board"]
        width, height = board["width"], board["height"]
        you = game_state["you"]
        head = (you["body"][0]["x"], you["body"][0]["y"])
        my_id = you["id"]
        my_len = len(you["body"])
        health = you.get("health", 100)

        food = board.get("food", [])

        blocked, heads, lengths, tails = _occupied_cells(board, my_id)

        candidates = []
        for name, (dx, dy) in DIRS.items():
            npt = (head[0] + dx, head[1] + dy)
            if not _in_bounds(npt, width, height):
                continue
            if npt in blocked:
                continue

            # Head-to-head risk check: if an opposing head could also move
            # onto npt next turn and that snake is >= our length, treat as
            # dangerous (skip unless no alternative).
            danger_h2h = False
            for sid, hpos in heads.items():
                if sid == my_id:
                    continue
                if _manhattan(hpos, npt) == 1:
                    # opponent could move into npt too
                    if lengths.get(sid, 0) >= my_len:
                        danger_h2h = True
                        break

            candidates.append((name, npt, danger_h2h))

        if not candidates:
            # No in-bounds / non-body moves at all. Just try anything that
            # keeps us in bounds, ignoring body blocks (already dead anyway).
            for name, (dx, dy) in DIRS.items():
                npt = (head[0] + dx, head[1] + dy)
                if _in_bounds(npt, width, height):
                    return {"move": name}
            return {"move": "up"}

        safe_candidates = [c for c in candidates if not c[2]]
        pool = safe_candidates if safe_candidates else candidates

        # Score each candidate.
        best_name = None
        best_score = None
        # Full (uncapped) flood-fill: the board is small (<= a few hundred
        # cells even on big boards), so this is cheap and lets us actually
        # tell apart "leads to a big open region" vs "leads into a
        # medium-but-eventually-closing pocket" -- a low cap made those
        # look identical before, which contributed to self-trapping into
        # dead-end corridors/corners on long games (see round-0 loss
        # analysis in README_agent.md).
        my_tail = tails.get(my_id)
        food_cells = {(f["x"], f["y"]) for f in food}

        # Bodies of opposing snakes (for adversarial worst-case lookahead
        # below) -- only snakes that are still alive/on the board and are
        # at least roughly as big as us are worth defending against (a
        # much-shorter snake can't meaningfully wall us off since we'd
        # win any resulting head-to-head anyway, and modeling it just
        # wastes a little compute for no benefit).
        threat_bodies = []
        for snake in board["snakes"]:
            if snake["id"] == my_id:
                continue
            if lengths.get(snake["id"], 0) >= my_len - 1:
                threat_bodies.append(snake["body"])

        for name, npt, danger_h2h in pool:
            # If this move lands on food, our own tail will NOT vacate this
            # turn (snake grows instead of sliding forward) -- so treat our
            # tail cell as still blocked for this candidate's flood-fill,
            # otherwise we overestimate reachable space / wrongly think we
            # can still path back to our tail immediately. Missing this
            # caused a real self-trap death (see README_agent.md): the bot
            # picked a food cell believing it had plenty of room + a clear
            # tail-path, but eating froze the tail and the room collapsed
            # the very next turn.
            will_eat = npt in food_cells
            if will_eat and my_tail is not None and my_tail not in blocked:
                eff_blocked = blocked | {my_tail}
            else:
                eff_blocked = blocked
            space, reached_tail = _flood_fill(npt, eff_blocked, width, height, target=my_tail)

            # Adversarial 1-ply lookahead: consider that a nearby
            # equal-or-longer opponent doesn't just sit still -- it will
            # take ITS own next move too, and a shadowing/cornering
            # opponent can convert a currently-open-looking region into a
            # much smaller one by simply moving alongside us (e.g.
            # hugging a wall in parallel to cut off our only exit).
            # For each nearby threat snake, try each of its own physically
            # legal next moves and recompute our flood-fill space in that
            # hypothetical -- take the worst (minimum) case across all
            # threats' choices. This is what a single-snapshot flood-fill
            # cannot see and is exactly the failure mode that lost a real
            # match (see README_agent.md: our snake raced up a wall
            # column while a same-length opponent shadowed one column
            # over, and got sealed into the corner once the wall ran out
            # -- at the time, the immediate flood-fill looked fine because
            # it assumed the opponent wouldn't move).
            worst_space = space
            if threat_bodies:
                for opp_body in threat_bodies:
                    opp_moves = _opp_candidate_cells(opp_body, eff_blocked, width, height)
                    if not opp_moves:
                        continue
                    for opp_npt in opp_moves:
                        if opp_npt == npt:
                            # Already handled via danger_h2h; still worth
                            # reflecting as zero further space here.
                            continue
                        hyp_blocked = eff_blocked | {opp_npt}
                        hyp_space, _ = _flood_fill(npt, hyp_blocked, width, height, target=my_tail)
                        if hyp_space < worst_space:
                            worst_space = hyp_space

            score = 0.0
            # Space safety: heavily penalize tight spaces relative to our
            # length (getting trapped = death).
            if space < my_len:
                score -= 1000.0 * (my_len - space)
            elif space < my_len * 1.5:
                # Still risky-ish: comfortably more than our length is
                # much safer than "just barely" enough, especially since
                # our own tail continues occupying space as we move.
                score -= 20.0 * (my_len * 1.5 - space)
            score += min(space, width * height) * 2.0

            # Penalize moves whose safety depends on a threatening
            # opponent NOT moving smartly -- i.e. where the worst-case
            # (adversarial) reachable space is much smaller than the
            # optimistic snapshot space computed above. Hard-penalize if
            # even the worst case would trap us (worst_space < my_len,
            # same severity tier as the optimistic hard penalty above so
            # a real forced trap is never masked by an optimistic
            # snapshot), and apply a smaller continuous penalty
            # proportional to how much an adversarial opponent move could
            # shrink our room, to bias away from "races along a wall next
            # to a same-length-or-longer opponent" scenarios in general.
            if worst_space < my_len:
                score -= 800.0 * (my_len - worst_space)
            score -= 8.0 * max(0, space - worst_space)

            # Tail-chasing safety net: if we can still path to our own
            # tail (which is guaranteed to vacate soon), that's a strong
            # signal we won't immediately self-trap. Penalize losing that
            # property, especially once we're reasonably long -- BUT only
            # strongly when space is actually tight. On a wide-open board
            # (space is many multiples of our length), temporarily losing
            # tail-reachability for one turn (e.g. because eating food
            # freezes the tail this turn) is a non-issue and should NOT
            # be treated the same as a real cramped self-trap risk.
            # Historical bug: a flat -60 penalty here made the bot refuse
            # to eat ANY food whenever eating cost "tail reachability",
            # even with 100+ open cells available, causing it to circle
            # forever avoiding food and starve to death in real matches
            # (see README_agent.md for the sim_213/216/231/214/227
            # starvation-loss analysis this round). Fix: scale the
            # penalty/bonus down to ~0 once space is comfortably large
            # relative to our length.
            open_threshold = max(my_len * 4, 24)
            if my_tail is not None and my_len >= 4:
                if reached_tail:
                    score += 15.0
                else:
                    # Losing tail-reachability is only "harmless" when the
                    # SPECIFIC cause is our own food-freeze adjustment above
                    # (eating this turn artificially blocks the tail cell
                    # for this one BFS, even though the board is wide open
                    # and the tail will still vacate as normal in reality).
                    # In ALL other cases (i.e. genuine structural reasons --
                    # the candidate cell just doesn't have a real path back
                    # to our tail because our own coiled body walls it off),
                    # losing tail-reachability is a real self-trap warning
                    # sign REGARDLESS of how big raw `space` looks right
                    # now -- a long spiral can have 90+ "open" cells that
                    # are actually a single dead-end pocket that our own
                    # advancing tail will seal off a few turns later.
                    # Real loss analysis (see README_agent.md): a 23-long
                    # snake at turn 114 had two candidates both reporting
                    # space=90/91 (>> open_threshold), one with
                    # reached_tail=True and one False (non-food-related);
                    # the old code gated the penalty down to a negligible
                    # +3/0 tie-break purely because space was "big", picked
                    # the reached_tail=False branch anyway, and spiraled
                    # into a sealed pocket 2 turns later with zero legal
                    # moves. Gating must be scoped to the food-freeze cause
                    # only, not to "space happens to be large".
                    if will_eat and space >= open_threshold:
                        score += 0.0
                    else:
                        score -= 60.0

            # Food attraction. Urgency scales smoothly and aggressively as
            # health drops -- starving to death is a *guaranteed* loss, so
            # once health is critically low we should strongly prefer
            # eating even if it costs some space/tail-reachability safety
            # margin (as long as it doesn't walk us into < my_len space,
            # which is still hard-penalized above).
            if food:
                dists = [_manhattan(npt, (f["x"], f["y"])) for f in food]
                nearest = min(dists)
                # Weight food urgency higher when health is low. Smooth,
                # steep ramp: mild early on, very large once health is
                # critically low (guaranteed starvation otherwise).
                if health <= 60:
                    urgency = 1.0 + 8.0 * ((60 - health) / 60.0) ** 2
                else:
                    urgency = 1.0
                score += urgency * (20.0 / (nearest + 1))
                # Extra flat bonus for a move that eats RIGHT NOW when
                # health is getting low -- guarantees survival progress
                # instead of just "closer is better", which matters once
                # nearest==0 vs nearest==1 should be a much bigger gap
                # than the 1/(n+1) curve alone provides at low health.
                if nearest == 0 and health <= 60:
                    score += 40.0 * ((60 - health) / 60.0)
            else:
                cx, cy = (width - 1) / 2.0, (height - 1) / 2.0
                score -= 0.1 * _manhattan(npt, (cx, cy))

            # Slight preference against hugging edges (more escape routes).
            edge_dist = min(npt[0], width - 1 - npt[0], npt[1], height - 1 - npt[1])
            score += 0.3 * edge_dist

            if danger_h2h:
                score -= 500.0

            # Tiny randomness to break ties unpredictably.
            score += random.uniform(0, 0.01)

            if best_score is None or score > best_score:
                best_score = score
                best_name = name

        return {"move": best_name}
    except Exception:
        return {"move": "up"}


if __name__ == "__main__":
    from server import run_server

    run_server({"info": info, "start": start, "move": move, "end": end})
