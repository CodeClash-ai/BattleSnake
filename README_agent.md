# Round 1 notes (current opponent ChaelCodes__cornelius, gpt-5-5)

- `/logs/rounds/0` result: `gpt-5-5` beat `ChaelCodes__cornelius` 204-43 with 3 draws. Opponent is a strong long-game snake: avg final turn ~193, max 492; movement is mostly vertical but uses all directions (vertical deltas ~38k, horizontal ~10k).
- Losses are mixed close/endgame failures rather than a single wall-crasher pattern. Final length diffs in non-wins cluster around tied/±3, with a few far-ahead self-coils. A short inspected loss (`sim_84`) showed us at length 9 and healthy choosing a two-exit bottom-edge move with very poor shallow self-continuation (`pc=7`, tail distance 14) over a one-exit but much more tail-connected/open continuation toward center/food (`pc=67`, tail distance 8), then riding the left rail to death.
- Kept one small generic defensive tweak: shallow self-avoidance/tail-connectivity lookahead now starts at `my_len >= 8` instead of `>= 10` when healthy. This changes `sim_84` t51 from `left` to `right`, while preserving the existing scoring machinery and not adding a new matchup-specific rule. Goal is to catch mid-length rail/noose choices before they become forced endgames.
- Validation: `python3 -m py_compile main.py`; local smoke `python3 tools/smoke_local.py food 50` -> 48 wins / 2 losses / 0 draws (rerun 49/1/0); `python3 tools/smoke_local.py up 20` -> 20/20 wins. Full replay over all long logs timed out under the 30s shell limit (expected with current lookahead), but a quick 3000-state replay sample over `/logs/rounds/0` returned 0 bad move strings.
- If future results regress from over-penalizing early corridors or runtime, revert the lookahead gate near line ~412 from `my_len >= 8` back to `>= 10`. If losses persist, inspect close-length long losses (`sim_206`, `sim_29`, `sim_117`, `sim_145`) for whether we need stronger tail-path/noose detection or more catch-up food.

# Round 1 notes (current opponent MorganConrad__tantilla, gpt-5-5)

- `/logs/rounds/0` result: `gpt-5-5` beat `MorganConrad__tantilla` 202-48. This is a strong balanced long-game survivor (opponent deltas nearly even; avg final turn ~297, max 620).
- Losses are overwhelmingly late self-coil deaths while we are safely ahead and healthy/mid-health: typical final states are us length 20-45 vs opponent length 6-13 with lots of food on the board. Examples: `sim_0` dies trapped in the top-left after taking a snack at t217 while +15 length; `sim_110` reaches length 46 vs 13 and has no legal escape at t568.
- Kept a defensive `main.py` retune for this matchup: once we are clearly far ahead (`len >=18`, `>= enemy + 8`) and health is not urgent (`>45`), tail connectivity is scored more strongly even below the old `health >70` gate, and no-path-to-tail moves get an extra penalty. Also broadened the far-ahead anti-food rule from `health >55` to `>45` so mid-health + huge-lead snakes stop taking optional snacks. Goal is to preserve an unwind path instead of growing into a dense noose.
- Validation this round: `python3 -m py_compile main.py`; local smoke `python3 tools/smoke_local.py up 20` -> 20/20 wins; `python3 tools/smoke_local.py food 50` -> 46 wins / 4 losses / 0 draws. Full replay over all 250 long logs timed out under the 30s shell limit, expected with current lookahead.
- If future results regress by starvation or failing to build an early lead, soften the new `far_ahead_cruise` block around the tail-connectivity code or restore the anti-food health threshold to 55. If losses remain late huge-length self-coils, go further toward explicit tail-following/endgame cruising once +8 length ahead.

# Round 1 notes (current opponent jackisherwood__battlesnake-elon, gpt-5-5)

- `/logs/rounds/0` result: `gpt-5-5` beat `jackisherwood__battlesnake-elon` 219-29 with 2 draws. This is a strong balanced long-game opponent: movement deltas are evenly spread and games average ~245 turns (max 507).
- Losses are mostly long coil/endgame failures rather than openings. Final states are often close length or us somewhat ahead, but several losses begin while we are equal/shorter and healthy, then we choose a one-exit move through our own coil because flood-fill still reports ~50 cells. Example `sim_0`: at t323 length 27 vs 29, old scoring chose `left` (one exit) and we were forced into a tiny pocket by t327; the new scoring chooses the two-exit `right` instead.
- Kept one conservative `main.py` tweak: for long healthy snakes (`len >=14`, `health >65`), non-food one-exit moves in cramped regions already had a small penalty; when we are not longer than the opponent, this penalty is now much stronger. Goal: prefer comparable two-exit/open continuations in close/behind endgames versus this balanced snake. Food/hungry routes and clear length-lead positions are not affected by the new subcondition.
- Validation this round: `python3 -m py_compile main.py`; `python3 tools/smoke_local.py up 30` -> 30/30; `python3 tools/smoke_local.py food 50` -> 47/3/0. Full replay over `/logs/rounds/0` timed out under the shell limit due the long 250-game log set and existing lookahead, but compile and smoke passed.
- If future results regress, reduce the new extra one-exit penalty in the block around the comment mentioning battlesnake-elon. If losses continue, inspect other long losses (`sim_17`, `sim_64`, `sim_136`, `sim_43`) for tail-connectivity/noose decisions; the opponent is strong enough that pure edge-food heuristics are probably not the main issue.

# Round 2 notes (current opponent coreyja__gigantic-george, gpt-5-5)

- New `/logs/rounds/1` is similar/slightly worse than round 0: we beat gigantic-george 184-66 (round 0 was 186-64). Games are very long (avg final turn ~319, max 748). Opponent moves in all directions and survives as a tiny snake while food accumulates.
- Losses are overwhelmingly self-coil/noose deaths after we are safely ahead: round-1 losses averaged length ~33 vs opponent ~9 and health ~98. Several short losses (e.g. `sim_44`) show the key local pattern: while far ahead and healthy, we choose non-food moves with `self_path_count` 0-1 / no tail path into a forced coil, then a later forced food/edge step kills us.
- Kept a defensive `main.py` tweak in the long/healthy lookahead block: when healthy, length >= opponent + 8, and a non-food candidate has fewer than 4 shallow self-avoiding continuations, apply a very large noose-throat penalty (extra on edge). Also made no-path-to-tail in far-ahead cramped areas much more punitive. This changes `rounds/1/sim_44` t196 from continuing right along the trap to taking bottom food instead; target is preserving mobility, not more growth.
- Added `tools/score_debug.py` for future analysis; it prints candidate diagnostics (area/exits/path_count/tail distance) for a logged state. It is simplified and not a perfect full-score clone, but useful to spot noose signatures.
- Validation: `python3 -m py_compile main.py`; local smoke `python3 tools/smoke_local.py up 30` -> 30/30, `python3 tools/smoke_local.py food 50` -> 46/4/0. Full replay over both long log sets timed out under the 30s shell limit after the added lookahead penalties; this is expected with 70k+ long states.
- If future results regress, the most likely cause is the new penalty being too strong for forced non-food corridors. Soften the `path_count < 4` block around lines ~423. If losses remain similar, consider a true tail-following/endgame policy once length >20/+8 rather than more anti-food scoring.

# Round 2 notes (current opponent coreyja__eremetic-eric, gpt-5-5)

- New `/logs/rounds/1` improved only slightly over round 0: `gpt-5-5` beat `coreyja__eremetic-eric` 164-85 with 1 draw (round 0 was 158-90-2). This is still a difficult long-endgame matchup; avg final turn ~338 and many games last 400-700 turns.
- Loss analysis confirms the same dominant failure mode as the prior handoff: we usually win the length race by a huge margin, then lose to our own dense coil/noose while the opponent remains tiny (losses avg max length ~40 in round 1, with many length 50-65 vs opponent ~8-12). Wins have much lower avg max length (~23), suggesting overgrowth is the problem.
- Kept one targeted `main.py` retune: when healthy (`health > 55`), length >=20, and already at least 8 longer than the opponent, treat reachable food as a liability with strong penalties (especially immediate food). This broadens the previous anti-food rule that only activated at length >=24/+12 and was not strong enough for eremetic-eric. Goal: stop bloating once the length race is safely won and preserve tail mobility/open space.
- Validation: `python3 -m py_compile main.py` passes. Full `replay_moves.py` over both long log sets timed out in the 30s shell limit (expected due self-lookahead over 500+ turn games). Local smoke after the change: `python3 tools/smoke_local.py up 10` -> 10/10 wins; `python3 tools/smoke_local.py food 20` -> 19/1; `python3 tools/smoke_local.py food 50` -> 44/6/0. The 50-food smoke is a bit worse than prior 46/4 samples, but this change is opponent-specific for a matchup where over-eating is clearly losing many games.
- If future logs show starvation or failure to build an early lead, soften the new far-ahead anti-food block around the food scoring section. If losses remain huge-length self-coils, the next improvement should be explicit path-to-tail / noose detection rather than more food collection.


# Round 1 notes (current opponent coreyja__eremetic-eric, gpt-5-5)

- `/logs/rounds/0` is a hard matchup: `gpt-5-5` beat `coreyja__eremetic-eric` only 158-90 with 2 draws. Games are very long (avg final turn ~351, max 744) and opponent movement is balanced/all-directions, so this is a real survival/endgame snake.
- Loss pattern is unusually consistent: by the last states we are usually massively ahead (often length 40-60 vs opponent length ~7-12, high health) but die in our own dense coil while the small opponent survives. This is not a growth problem; it is over-eating / tail-pinning / noose management once already far ahead. Example `sim_100`: from t347-t370 we eat many edge/outer foods, reach length 54 vs 7, then die in the bottom-right corner.
- Kept one targeted `main.py` tweak: when healthy, length >=24, and at least 12 longer than the opponent, penalize immediate/near food (extra penalty for immediate food). Goal is to stop turning a won position into an enormous self-trap; hungry or close-length states are unaffected.
- Validation this round: `python3 -m py_compile main.py`; local smoke `python3 tools/smoke_local.py up 10` -> 10/10 wins; `python3 tools/smoke_local.py food 20` -> 19 wins / 1 loss. Full `replay_moves.py /logs/rounds/0` was too slow after this change (self-lookahead on 500+ turn logs timed out), so I killed stale replay processes.
- Next ideas: build an endgame/tail-connectivity evaluator for very long snakes, or reduce far-ahead food seeking more if logs still show huge-length self-coil deaths. Watch for regression if we start losing by starvation or failing to build an early lead.

# Round 1 notes (current opponent moxuz__pinky-snek)

- `/logs/rounds/0` result: `gpt-5-5` swept `moxuz__pinky-snek` 250-0 across all 250 games. `tools/analyze_logs.py` reports avg final turn 46.22, min 7, max 359.
- Opponent profile from `tools/opponent_profile.py`: starts across the standard positions and moves in all directions almost evenly (`left=2850`, `down=2846`, `up=2830`, `right=2780`), so it is not a trivial straight-wall bot. The current survival/space/anti-edge bot still handles it perfectly in the known logs.
- I made no `main.py` strategy changes this round. With a perfect logged match, preserving the tuned policy is safer than speculative retuning.
- Validation/smoke this round: `python3 -m py_compile main.py`; `python3 tools/replay_moves.py /logs/rounds/0` -> `checked_states=5721 bad=0`; `python3 tools/smoke_local.py up 20` -> 20/20 wins; `python3 tools/smoke_local.py food 50` -> 45 wins / 5 losses / 0 draws.
- Recommendation for next teammate: keep `main.py` stable unless new logs show actual losses/draws. If failures appear, inspect the longest games first (current max turn 359) for late self-coil/tail-following or optional edge-food issues; otherwise current code is already sweeping this opponent.

# Round 1 notes (current opponent Spenca__vulture-snake)

- `/logs/rounds/0` result: `gpt-5-5` beat `Spenca__vulture-snake` 247-1 with 2 draws across 250 games. Opponent moves horizontally more than vertically but uses all directions (`left=3252`, `right=3143`, `up=2138`, `down=2030`), so not a simple wall-crasher.
- The only loss was `/logs/rounds/0/sim_36.jsonl`. We were healthy but clearly shorter (7 vs 11), rode the right edge downward into the bottom-right corner, then ate bottom-edge food while the longer opponent paralleled us on y=2 and swept left; we eventually died trapped on the bottom-left.
- Kept one targeted `main.py` tweak: when healthy and at least 2 length behind, if already on the actual edge, penalize non-food edge moves that continue toward a corner. This changes the replayed loss at turn 82 from `down` to `up`, trying to break the rail squeeze before the corner. It is disabled for food/hungry moves and only applies to actual-edge-to-actual-edge corner-approach moves.
- Validation after change: `python3 -m py_compile main.py`; `python3 tools/replay_moves.py /logs/rounds/0` -> `checked_states=5387 bad=0`; local smoke `python3 tools/smoke_local.py up 30` -> 30/30 wins; `python3 tools/smoke_local.py food 50` -> 46 wins / 4 losses / 0 draws (baseline rerun before the tweak was 47/3/0, so this is a small acceptable risk for the observed rail-squeeze loss).
- If future results regress, consider softening/removing the new block just before the "Stay central/open" comment. If future losses persist, inspect same pattern: shorter/healthy snake riding outer rail while opponent shadows the adjacent lane.

# Round 1 notes (current opponent rdbrck__btas)

- Only `/logs/rounds/0` is present for this matchup. Result was a clean sweep: `gpt-5-5` beat `rdbrck__btas` 250-0 across all 250 games. `tools/analyze_logs.py` reports avg final turn 46.27, min 5, max 226.
- Opponent movement is varied/all-directions by simple delta profile (`down=3594`, `up=3429`, `left=2152`, `right=2142`), not a trivial wall-crasher, but the current survival/space/anti-edge bot handles it reliably.
- I made no `main.py` strategy changes this round. With a perfect logged match, preserving the tuned current policy is lower risk than speculative retuning.
- Validation/smoke this round: `python3 -m py_compile main.py`; `python3 tools/replay_moves.py /logs/rounds/0` -> `checked_states=5994 bad=0`; `python3 tools/smoke_local.py up 20` -> 20/20 wins; `python3 tools/smoke_local.py food 50` -> 47 wins / 3 losses / 0 draws.
- Recommendation for next teammate: keep `main.py` stable unless future logs show actual losses. If failures appear, inspect the longest games (round 0 max turn 226) for late self-coil/tail-following or edge/rail issues; otherwise current code is already sweeping this opponent.

# Round 1 notes (current opponent zacpez__scape-goat)

- `/logs/rounds/0` is present for this matchup. Result was a clean sweep: `gpt-5-5` beat `zacpez__scape-goat` 250-0 across all 250 games. `tools/analyze_logs.py` reports avg final turn 41.87, min 5, max 255.
- Opponent is not a simple straight-wall bot by deltas (`up=2611`, `right=2550`, `down=2534`, `left=2523` in `tools/opponent_profile.py`), but the current survival/space bot already handles it reliably.
- I made no `main.py` strategy changes this round. Given a perfect logged match, preserving the current tuned survival/anti-edge/food behavior seems lower risk than retuning.
- Validation/smoke this round: `python3 -m py_compile main.py`; `python3 tools/replay_moves.py /logs/rounds/0` -> `checked_states=5493 bad=0`; `python3 tools/smoke_local.py up 30` -> 30/30 wins; `python3 tools/smoke_local.py food 50` -> 47 wins / 3 losses / 0 draws.
- Recommendation for next teammate: keep `main.py` stable unless new logs show a loss pattern. If future losses occur against this opponent, inspect the long games (max turn 255) for late self-coil/tail-following issues; otherwise current code is already sweeping.


Round 1 notes (current opponent coreyja__jump-flooding):

- `/logs/rounds/0` has 250 non-empty games. Result: `gpt-5-5` beat `coreyja__jump-flooding` 242-6 with 2 draws. Opponent is a real food/space bot (deltas spread across all directions), not a wall-crasher.
- Losses: `sim_35`, `sim_133`, `sim_191` are short edge/corner races while we are length 4 vs their length 5; `sim_138` is an equal/shorter top-left edge head race; `sim_178` is starvation after staying short; `sim_59` is a long game where we are badly shorter and eventually die near the lower-left. Draws `sim_24`/`sim_248` are mutual edge/corner eliminations.
- Kept one conservative `main.py` tweak: when we are shorter than the max enemy length, increase food urgency and add a small close-food bonus. Rationale: this opponent grows efficiently, and several failures begin after we fall 1+ length behind and then every edge/corner becomes a losing head-to-head. The tweak is off when we are ahead and only modest when equal.
- Validation after change: `python3 -m py_compile main.py`; `python3 tools/replay_moves.py /logs/rounds/0` -> `checked_states=2199 bad=0`.
- Local smoke after change: `python3 tools/smoke_local.py up 20` -> 20/20 wins; `python3 tools/smoke_local.py food 50` -> 47 wins / 3 losses / 0 draws (better than pre-change 45/5/0 on this run).
- Next ideas: if losses persist, inspect whether the new food urgency is still too weak around early length-4 vs length-5 states, or build a stronger local clone of jump-flooding. Be careful with edge-food penalties: this opponent can punish being shorter, so refusing too much food may be harmful.

# Round 1 notes (current opponent coreyja__coreyja-rs)

- Only `/logs/rounds/0` is present. Result: `gpt-5-5` swept `coreyja__coreyja-rs` 20-0 across the 20 non-empty games (230 empty sim files). `tools/analyze_logs.py` reports avg final turn 6.80, max 10.
- Opponent profile from `tools/opponent_profile.py`: starts at standard positions and almost always moves straight up (`(0, 1)=115`, only one observed downward move). It appears to be a simple wall-bound bot.
- I made no `main.py` strategy changes this round. The current conservative survival bot already cleanly beats the known opponent, so avoiding risky retuning seems best.
- Validation this round: `python3 -m py_compile main.py`; `python3 tools/replay_moves.py /logs/rounds/0` -> `checked_states=102 bad=0`.
- Local smoke this round: `python3 tools/smoke_local.py up 20` -> 20/20 wins; `python3 tools/smoke_local.py food 20` -> 19 wins / 1 loss / 0 draws.
- Recommendation: keep `main.py` stable unless new logs show a real loss pattern. If future rounds still face this opponent, straight-up smoke is the key regression check.

# Round 2 update (current opponent coreyja__bombastic-bob)

- New logs in `/logs/rounds/1`: `gpt-5-5` swept `coreyja__bombastic-bob` 250-0 across 250 games. This improved on round 0 (249-1). Opponent movement remains varied/all directions, not a trivial wall-crasher, but current survival/anti-rail code handled it cleanly.
- I made no `main.py` strategy change this round. Since the most recent anti-edge/rail tweaks appear to have fixed the single round-0 failure mode and produced a perfect round, reliability is preferable to retuning.
- Validation this round: `python3 -m py_compile main.py`; `python3 tools/replay_moves.py /logs/rounds/0` (`checked_states=4433 bad=0`); `python3 tools/replay_moves.py /logs/rounds/1` (`checked_states=6081 bad=0`).
- Local smoke using current code: `python3 tools/smoke_local.py up 20` -> 20/20 wins; `python3 tools/smoke_local.py food 50` -> 45 wins / 5 losses / 0 draws, matching the previous handoff.
- Recommendation: keep current `main.py` unless future logs show new losses. If losses return, first inspect optional edge food / one-exit rail moves while healthy and ahead; those were the only observed weakness in round 0.

# Round 1 update (current opponent coreyja__bombastic-bob)

- New logs in `/logs/rounds/0`: `gpt-5-5` beat `coreyja__bombastic-bob` 249-1 across 250 games. Opponent movement is varied/all directions; not a trivial wall-crasher. The only loss was `/logs/rounds/0/sim_177.jsonl`.
- Loss pattern: we were safely longer (5-6 vs 3) but grabbed optional top-edge food at turn 21 (`(8,10)`), then continued along the top rail into `(10,10)` and died because our own body/enemy body left no exit. A stronger play at t21 is to move right into/near the shorter enemy head; in the actual log that likely wins head-to-head immediately instead of eating.
- Kept two conservative `main.py` tweaks targeting that exact failure:
  1. Optional edge-food penalty now applies when healthy and at least `max_enemy_len + 2` (was +3) and is slightly stronger (-65 vs -45). This makes replay choose `right` instead of eating in `sim_177` turn 21.
  2. Healthy non-food rail moves with only one exit now get a larger penalty, with an extra near-corner penalty. This makes replay choose `left` instead of continuing along the top rail in `sim_177` turn 22.
- Validation after the change: `python3 -m py_compile main.py`; `python3 tools/replay_moves.py /logs/rounds/0` -> `checked_states=4433 bad=0`.
- Local smoke after the change: `python3 tools/smoke_local.py up 20` -> 20/20 wins; `python3 tools/smoke_local.py food 50` -> 45 wins / 5 losses / 0 draws. This is comparable to recent handoffs, though not a perfect regression test.
- Recommendation: keep watching for optional edge/rail snacks while ahead. If future logs show missed critical growth near the edge, soften the edge-food penalty around the `edge_food` block.

# Round 2 update (current opponent nbw__nbw-crystal)

- New logs in `/logs/rounds/1`: `gpt-5-5` beat `nbw__nbw-crystal` 244-2 with 4 draws across 250 games. This is slightly worse than round 0 (247-2-1) but still a strong win. Losses were `/logs/rounds/1/sim_56.jsonl` and `sim_80.jsonl`; draws were `sim_102`, `sim_144`, `sim_212`, `sim_215`.
- Pattern in losses/draws: when healthy and roughly equal length, we sometimes drift around the outer rail while the opponent is nearby/equal-or-longer, then get forced into a corner/edge head-to-head or mutual death. This is the same family as the previous round's edge/corner races.
- Kept one conservative `main.py` tweak: add an extra penalty for healthy, non-food moves on the outer ring when an equal-or-longer (or only one shorter) enemy head is within 5 cells and we are not clearly longer. It is disabled when hungry/eating and when we have a clear length lead. Goal: prefer the inner lane during optional same-size wall races.
- Validation after the change: `python3 -m py_compile main.py`; `python3 tools/replay_moves.py /logs/rounds/0` (`checked_states=1848 bad=0`); `python3 tools/replay_moves.py /logs/rounds/1` (`checked_states=1727 bad=0`).
- Local smoke after the change: added `tools/smoke_local.py`; results were 20/20 wins vs `simple_opponent.py up`, and 45 wins / 4 losses / 1 draw vs `simple_opponent.py food` seeds 1-50. This is not worse than prior handoff (44/4/2), so the edge-race penalty seems safe.
- Recommendation: keep focusing on edge/corner race avoidance vs this opponent. If future logs get worse, inspect whether the new outer-ring penalty blocks necessary food or escape routes; otherwise next best improvement is a deeper simulation of equal-length head pressure near corners.

# Agent notes for next teammate

Current repository status for gpt-5-5 Battlesnake:

- Completed match logs available: `/logs/rounds/0`.
- Round 0 result: won 20-0 against `csauve__bookworm`.
- Opponent profile from round 0: `csauve__bookworm` mostly drives vertically until it hits a wall. Starts in top half go down; starts elsewhere go up. It never beat us in non-empty logs.
- Round 2 review: I re-checked the logs and re-ran validation/smoke tests. Because the current bot already swept the known opponent and the opponent appears extremely exploitable, I made no `main.py` strategy change this round (reliability > risky tuning).

Useful helper scripts:

- `python3 tools/analyze_logs.py /logs/rounds/<n>` summarizes non-empty logs, winners, and final turns.
- `python3 tools/opponent_profile.py /logs/rounds/<n>` counts opponent start positions and observed move deltas.
- `python3 tools/inspect_round.py /logs/rounds/<n>` prints the first non-empty game turn-by-turn for quick manual inspection.
- `python3 tools/replay_moves.py /logs/rounds/<n>` replays current `main.move` over logged states and checks it always returns a valid direction.
- `tools/simple_opponent.py` is a tiny Flask opponent for local smoke tests, e.g. start our server and `python3 tools/simple_opponent.py up 8001`, then use `./game/battlesnake play ...`.

Bot status:

- Main player code is `main.py`.
- Strategy is a compact safety-first flood-fill/Voronoi survival bot with head-to-head avoidance, center/open-space preference, and food urgency.
- Previous teammate made one conservative change: when health <= 30, reachable food distance gets an extra direct score penalty/bonus so the bot is less likely to let flood-fill area dominate and starve in longer games. This should not affect the short current-opponent games unless health is genuinely low.
- Given current logs, reliability is the priority. Avoid risky aggression unless future logs show a stronger opponent.

Testing performed in round 2:

- `python3 tools/analyze_logs.py /logs/rounds/0` confirms all 20 non-empty games were wins.
- `python3 tools/opponent_profile.py /logs/rounds/0` confirms the opponent's vertical straight-line behavior: deltas `(0, 1)` and `(0, -1)` only.
- `python3 -m py_compile main.py` passes.
- `python3 tools/replay_moves.py /logs/rounds/0` passes (`checked_states=59 bad=0`).
- Local CLI smoke tests this round: 10/10 wins vs `tools/simple_opponent.py up`; 50/50 wins vs a temporary greedy head-chasing opponent; 43/50 wins vs `tools/simple_opponent.py food`. Known opponent is much weaker than these local tests.

Next ideas if the opponent gets stronger:

- Add a deeper 2-ply/minimax opponent simulation for head-to-heads and trap avoidance.
- Build more local regression opponents (wall-hugger, tail-chaser, aggressive head-to-head) and run many seeded games before changing scoring weights.
- Consider adding dead-end/corridor detection for long games; in local tests vs the greedy food opponent, some losses came from eventually following a wall corridor into a self/enemy-body pocket.
- Be careful not to make the bot too aggressive: current wins come from staying alive while simple opponents self-eliminate.

Round 1 (current handoff) notes:

- I reviewed `/logs/rounds/0` again: scoreboard says `gpt-5-5` beat `coreyja__improbable-irene` 20-0; non-empty logs are still all wins. Opponent movement profile from logs is almost entirely straight upward with one left delta, so the current conservative survival bot is already well matched.
- Validation run this round: `python3 -m py_compile main.py` and `python3 tools/replay_moves.py /logs/rounds/0` both passed (`checked_states=47 bad=0`).
- Local smoke test vs `tools/simple_opponent.py up`: 30/30 wins.
- I briefly tried adding a second-step flood-fill tie-breaker to avoid future corridor traps. It preserved 30/30 vs straight-up but worsened local greedy-food results (45/50 vs the previous ~48/50 on seeds 1-50), so I reverted it. No strategy changes are currently pending.
- Recommendation: keep reliability unless future logs show a stronger or different opponent. If experimenting, compare across fixed seed ranges vs `simple_opponent.py food` and the known straight-line profile before keeping changes.

Round 2 handoff notes:

- New logs are present in `/logs/rounds/1`. Result again favors us: `gpt-5-5` beat `coreyja__improbable-irene` 18-0. The 18 score matches the 18 non-empty sim logs; every non-empty logged game was a win.
- Re-ran log tools: `/logs/rounds/1` opponent deltas are almost all `(0, 1)` with a few `(1, 0)`, i.e. still a wall-bound straight-line/simple bot. Average game lasted only 6.56 turns.
- Validation this round: `python3 -m py_compile main.py`, `python3 tools/replay_moves.py /logs/rounds/0`, and `python3 tools/replay_moves.py /logs/rounds/1` all pass.
- Local smoke this round using current code: 30/30 wins vs `tools/simple_opponent.py up` on seeds 1-30; 44/50 wins, 4 losses, 2 draws vs `tools/simple_opponent.py food` on seeds 1-50. No `main.py` change kept; the known opponent remains much weaker than the greedy-food smoke opponent.
- Caution: when scripting CLI tests, `battlesnake play` logs to stderr, so capture `2>&1` before grepping for winners.

Round 1 (this handoff, graeme-hill__snakebot logs) notes:

- Only `/logs/rounds/0` was present this round. Result: `gpt-5-5` beat `graeme-hill__snakebot` 91-1 across 92 non-empty games (158 empty files). `python3 tools/analyze_logs.py /logs/rounds/0` reports avg final turn 17.83, min 2, max 237.
- Opponent profile is no longer the previously documented straight-only bot; observed deltas are spread across all directions: `(0,1)=556`, `(0,-1)=368`, `(1,0)=319`, `(-1,0)=306`. Still, we dominated 91-1.
- The single loss was `/logs/rounds/0/sim_248.jsonl`. We were ahead 23 length vs 17, ate unnecessary bottom-edge food at turn 169, pinned our tail, then spiraled into the lower-left corner and died on turn 185 while opponent survived. Current code replay of that logged state now chooses `left` at turn 169 rather than eating at `(4,0)`.
- Kept one conservative `main.py` tweak: when healthy and already at least 3 longer, immediate food on the board edge gets a small penalty, and the existing healthy/far-ahead near-food penalty was slightly broadened (`>= max_enemy_len + 4`, -25). Goal is to avoid optional wall snacks that can initiate self-traps without changing hungry/equal-length behavior.
- Validation this round: `python3 -m py_compile main.py` passes; `python3 tools/replay_moves.py /logs/rounds/0` passes (`checked_states=1238 bad=0`). Local smoke tests with the changed code: 30/30 wins vs `tools/simple_opponent.py up` seeds 1-30; 46/50 wins, 2 losses, 2 draws vs `tools/simple_opponent.py food` seeds 1-50 (slightly better than previous handoff's 44/50 on the same smoke range, but not a perfect regression test).
- Recommendation: keep the conservative anti-edge-food tweak unless later logs show it costs early growth. For future improvements, focus on longer-game self-trap avoidance/tail-chasing once ahead; the known loss was not opponent aggression but our own wall spiral after eating.

Round 2 (current handoff, graeme-hill__snakebot) notes:

- New logs in `/logs/rounds/1`: `gpt-5-5` beat `graeme-hill__snakebot` 94-0 across 94 non-empty games (156 empty). Avg final turn 8.17, max 34. Opponent deltas still varied but it died quickly; no losses to inspect.
- I kept one small `main.py` change: added an extra edge penalty only when healthy (`health > 60`) and the candidate edge move's flood-fill area is under 45% of the board. This is aimed at the same failure mode as the previous anti-edge-food tweak (long wall spirals / self-traps) while still allowing edge corridors when hungry or spacious.
- Validation after the change: `python3 -m py_compile main.py`; `python3 tools/replay_moves.py /logs/rounds/0` (`checked_states=1238 bad=0`); `python3 tools/replay_moves.py /logs/rounds/1` (`checked_states=372 bad=0`).
- Local smoke after the change: 30/30 wins vs `tools/simple_opponent.py up` seeds 1-30; 45/50 wins, 3 losses, 2 draws vs `tools/simple_opponent.py food` seeds 1-50. I also tried simply increasing the wall penalty from 12 to 25, but that was worse (43/50 vs food), so I reverted to the conditional penalty.
- Note for local test scripts: winner log says `X was the winner` (not `X is the winner`).

Round 1 handoff notes (current opponent coreyja__devious-devin):

- Only `/logs/rounds/0` was present. Result: `gpt-5-5` beat `coreyja__devious-devin` 39-0 across all 39 non-empty logs (211 empty files). `tools/analyze_logs.py` reports avg final turn 6.08, max 10.
- Opponent profile: starts spread over standard positions, observed head deltas are almost entirely straight up: `(0, 1)=193`, with just 5 downward moves. It appears to run into the top wall quickly.
- I made no strategy change this round. Current safety-first bot is already sweeping the known opponent, and reliability seems more valuable than tuning against a simple wall-crasher.
- Validation this round: `python3 -m py_compile main.py` and `python3 tools/replay_moves.py /logs/rounds/0` passed (`checked_states=159 bad=0`).
- Local smoke: 100/100 wins vs `tools/simple_opponent.py up` seeds 1-100; 45/50 wins, 3 losses, 2 draws vs `tools/simple_opponent.py food` seeds 1-50.
- Recommendation: keep current `main.py` unless new logs show losses. If experimenting, use the fixed seed smoke ranges above and make sure straight-up remains a clean sweep.

Round 2 notes (current opponent coreyja__devious-devin):

- New logs in `/logs/rounds/1`: `gpt-5-5` beat `coreyja__devious-devin` 20-0 across all 20 non-empty logs (230 empty files). Avg final turn 7.00, min 2, max 11.
- Opponent profile remains extremely simple/wall-bound: `/logs/rounds/1` deltas were mostly straight up `(0, 1)=93`, with some down/left noise `(0, -1)=18`, `(-1, 0)=9`. It still dies quickly.
- I made no `main.py` strategy change this round. Current bot already swept both known rounds (39-0 and 20-0), and reliability against this weak opponent is more valuable than tuning.
- Validation this round: `python3 -m py_compile main.py`; `python3 tools/replay_moves.py /logs/rounds/0` (`checked_states=159 bad=0`); `python3 tools/replay_moves.py /logs/rounds/1` (`checked_states=85 bad=0`).
- Local smoke using current code: 50/50 wins vs `tools/simple_opponent.py up` seeds 1-50; 44/50 wins, 4 losses, 2 draws vs `tools/simple_opponent.py food` seeds 1-50.
- Recommendation: keep `main.py` stable unless future logs show losses or a new opponent strategy. If experimenting, benchmark against fixed seed ranges and ensure the straight-up smoke opponent remains a clean sweep.

Round 1 notes (current opponent m-schier__kreuzotter):

- `/logs/rounds/0` result: `gpt-5-5` beat `m-schier__kreuzotter` 28-2 across 30 non-empty games. Opponent movement is varied, not just a wall-crasher: deltas roughly up=218, left=120, down=119, right=112. Losses were `sim_230.jsonl` (turn 269) and `sim_236.jsonl` (turn 149); both were long games where we were ahead but self-trapped in/near our own coil while the opponent survived.
- I tried a tail-connectivity/noose penalty for healthy long snakes. It passed replay but worsened local greedy-food smoke from 44/50 to 43/50, so I reverted it.
- Kept one small conservative `main.py` change: the bonus for moving into a shorter snake's possible head square is now reduced from +40 to +12 when we are already more than 3 length ahead. This should reduce unnecessary chase pressure into cramped patterns while preserving close-length head-to-head aggression. Local smoke improved slightly vs `tools/simple_opponent.py food` seeds 1-50 (45 wins, 4 losses, 1 draw vs original 44/4/2) and remained 30/30 vs `simple_opponent.py up`.
- Validation: `python3 -m py_compile main.py`, `python3 tools/replay_moves.py /logs/rounds/0` (`checked_states=347 bad=0`), local smoke as above.
- Next ideas: inspect losses in new logs for self-trap patterns; a robust tail-chasing/dead-end detector would be valuable, but benchmark carefully because a simple tail-distance penalty made local results worse.

Round 2 notes (current opponent m-schier__kreuzotter):

- New logs in `/logs/rounds/1`: `gpt-5-5` beat `m-schier__kreuzotter` 33-1 across 34 non-empty games. The only loss was `/logs/rounds/1/sim_242.jsonl`, a long self-coil/noose death at turn 163 while far ahead (15 vs 7). We again lost by chasing/pressuring near the smaller snake and coiling into our own body, not by starvation or direct head-to-head.
- Kept a defensive `main.py` change for this pattern: added `self_path_count()` shallow self-avoidance lookahead for long/healthy snakes, and reduced/removed close-enemy chase bonuses when we are far ahead (`> max_enemy_len + 6`). This is intended to make open-space survival beat unnecessary pursuit of a much shorter opponent.
- Validation after the change: `python3 -m py_compile main.py`; `python3 tools/replay_moves.py /logs/rounds/0` (`checked_states=347 bad=0`); `python3 tools/replay_moves.py /logs/rounds/1` (`checked_states=220 bad=0`).
- Caveat: local CLI smoke testing hung in this environment after a timed-out command left stale processes; I killed the stale servers. If you run local smoke, first check `ps -ef | grep battlesnake` and use generous timeouts.
- Next idea: a stronger version would simulate following our tail / reject moves that have no path to tail in long healthy games. Be careful: earlier simple tail-distance penalties hurt local greedy-food results.

Round 1 notes (current opponent nbw__nbw-crystal):

- `/logs/rounds/0` had 250 non-empty games: `gpt-5-5` won 247, `nbw__nbw-crystal` won 2, and 1 draw. Avg final turn 13.33, max 89. Opponent movement is varied rather than a trivial wall-crasher.
- Losses were `/logs/rounds/0/sim_154.jsonl` and `/logs/rounds/0/sim_233.jsonl`; draw was `/logs/rounds/0/sim_242.jsonl`. The losses were short/medium edge-corner races where we were healthy but drove along the outer rail with only one immediate exit, eventually leaving only a bad equal/longer head-to-head/corner move.
- Kept one conservative `main.py` tweak: if healthy (`health > 55`), on the board edge, not eating, and the candidate has <=1 immediate exit, apply an extra -45 penalty. This is meant to prefer the parallel interior lane and avoid optional rail/corner races while still allowing hungry food runs and spacious edge moves.
- Validation after the change: `python3 -m py_compile main.py`; `python3 tools/replay_moves.py /logs/rounds/0` passed (`checked_states=1848 bad=0`). Local smoke: 30/30 wins vs `tools/simple_opponent.py up` seeds 1-30; 44/50 wins, 4 losses, 2 draws vs `tools/simple_opponent.py food` seeds 1-50.
- Caveat: the tweak did not change the replayed choices at the exact late turns I inspected (`sim_154` t47, `sim_233` t73), because other terms still favored the logged move. It may still help earlier/tie states, but future teammates should verify against new logs and consider reverting if performance drops.

Round 1 notes (current opponent Xe__since):

- `/logs/rounds/0` result: `gpt-5-5` beat `Xe__since` 247-2 with 1 draw across 250 games. Losses are `sim_92.jsonl` and `sim_113.jsonl`; draw is `sim_180.jsonl`. Opponent is varied (all four deltas roughly equal), not a wall-crasher.
- The two losses are long/medium games where we got into self-coil/corner pockets while the opponent was longer. In `sim_113`, an immediate food at turn 82 led into a small loop; by turn 85/86 there were no genuinely safe choices left. In `sim_92`, we were length 18 vs 21 and eventually lost a close head/corner race around the left side.
- Kept one small correctness fix in `main.py`: the shallow `self_path_count` lookahead now models immediate eating correctly by keeping our tail and removing the eaten food. The previous version always dropped the tail for lookahead, making snack moves inside/near a coil look safer than they are.
- Validation: `python3 -m py_compile main.py`; `python3 tools/replay_moves.py /logs/rounds/0` (`checked_states=11586 bad=0`). Local smoke after the fix: 30/30 wins vs `simple_opponent.py up`; 43/50 wins, 6 losses, 1 draw vs `simple_opponent.py food` seeds 1-50. This food smoke is a bit worse than prior handoff, so if future logs regress consider reverting just this self-lookahead tail-growth fix, but it targets the observed self-coil failure mode.
- I also tried an extra penalty for healthy immediate food with few exits; it changed `sim_113` turn 82 from eating to escaping, but worsened the greedy-food smoke further (41/50), so I reverted that penalty.

Round 2 notes (current opponent Xe__since, current handoff):

- New logs in `/logs/rounds/1`: we still won clearly, but dropped to 239-11 (no draws) versus 247-2-1 in round 0. Losses are mostly long games where we are healthy but equal/shorter and get pulled into edge/corner head races or self-coils; examples: `sim_104` top-edge food at turn 140 leads to an unavoidable longer enemy head-to-head at (2,9), `sim_115` bottom-edge food/rail race, `sim_76` close equal-length food chase.
- Kept two defensive `main.py` tweaks:
  1. A one-turn-ahead head-trap penalty for healthy close-length states. It looks at plausible equal/longer enemy steps near the candidate and penalizes moves whose next continuations are all covered by that enemy's next head danger, especially on edges.
  2. An additional penalty for optional immediate edge food when healthy, still not longer after eating, and a longer/equal enemy head is within 4. This targets the repeated Xe__since rail-snack trap pattern while staying off for urgent starvation food.
- Validation: `python3 -m py_compile main.py`; `python3 tools/replay_moves.py /logs/rounds/0` -> `checked_states=11586 bad=0`; `python3 tools/replay_moves.py /logs/rounds/1` -> `checked_states=13165 bad=0`.
- Local smoke after changes: `python3 tools/smoke_local.py up 10` -> 10/10 wins; `python3 tools/smoke_local.py food 50` -> 45 wins / 5 losses / 0 draws (roughly comparable to prior 43/50 and this round's quick 17/20 sample, but not a definitive regression test).
- Caveat: the new penalties do not change the logged move in `sim_104` turn 140 (down is still selected because all legal moves are bad by then). They are intended to influence earlier/tie states; inspect future logs to decide whether to strengthen or revert. Next likely improvement is deeper minimax/rollout around equal-length head proximity near rails.

Round 1 notes (current opponent ccSnake2018__ccsnake):

- `/logs/rounds/0` result: `gpt-5-5` beat `ccSnake2018__ccsnake` 241-9 across 250 games. Opponent is varied/all directions (not a wall-crasher) and the remaining losses are mostly healthy edge/corner races where we are equal or shorter and get shadowed by a longer/equal head until the only rail exit is losing.
- Loss examples inspected: `sim_4`, `sim_62`, `sim_81`, `sim_126`, `sim_154`, `sim_180`, `sim_197`, plus longer `sim_38`/`sim_115`. Many final states show us on x=0/x=10/y=0/y=10 with the opponent close and equal/longer; some are direct head-to-head deaths, some are forced after following the rail.
- Kept a defensive `main.py` tweak: stronger optional edge-food penalty when eating still does not make us longer and an equal/longer enemy is within 4; added additional healthy/not-hungry penalties for moving into the outer ring/actual edge/corner near a close equal-or-longer snake, including same-edge rail-race detection. This is meant to bias toward the interior lane in the exact lost pattern while preserving starvation/clear lead behavior.
- Validation after the change: `python3 -m py_compile main.py`; `python3 tools/replay_moves.py /logs/rounds/0` -> `checked_states=9546 bad=0`.
- Local smoke after the change: `python3 tools/smoke_local.py up 50` -> 50/50 wins; `python3 tools/smoke_local.py food 50` -> 47 wins / 3 losses / 0 draws (better than recent 44-45/50 notes, though this smoke opponent is not the real opponent).
- Caveat: some exact late logged losing states are already doomed or still select the logged edge move because all alternatives score worse; the change is intended to alter earlier/tie states. If future results regress, consider reducing the new edge penalties around lines ~447 and ~470.

Round 2 notes (current opponent ccSnake2018__ccsnake, this handoff):

- New `/logs/rounds/1` result improved versus round 0 but still had rare failures: `gpt-5-5` beat `ccSnake2018__ccsnake` 245-4 with 1 draw across 250 games. Losses were `sim_46`, `sim_56`, `sim_73`, `sim_233`; draw was `sim_30`.
- Loss pattern remains consistent: while healthy but materially shorter (often 7-9 vs 11-12), we chase optional outer-ring/edge food or ride the rail. The longer opponent shadows an adjacent lane and eventually forces a losing head-to-head/corner squeeze. Examples: `sim_233` left edge, `sim_46`/`sim_56` right edge, `sim_73` bottom-left.
- Kept a conservative additional `main.py` bias for that pattern: when health > 70 and we are at least 2 length behind, outer-ring immediate food is discounted and all outer-ring/edge moves get an extra penalty. This is meant to prefer the interior lane when food is not urgent and growth will not catch us up.
- Validation after the change: `python3 -m py_compile main.py`; `python3 tools/replay_moves.py /logs/rounds/0` -> `checked_states=9546 bad=0`; `python3 tools/replay_moves.py /logs/rounds/1` -> `checked_states=8459 bad=0`.
- Local smoke after tuning: `python3 tools/smoke_local.py up 30` -> 30/30 wins; `python3 tools/smoke_local.py food 50` -> 46 wins / 4 losses / 0 draws. An earlier stronger version of this penalty got only 44/50 vs food, so I softened it before keeping.
- Caveat: current-code replay now chooses interior moves before the late losing rail states in several losses, but replay is not a real alternate simulation. If future logs regress, reduce the new penalties near the comments mentioning "substantially shorter" / "outer-lane races".

Round 2 update (current opponent coreyja__coreyja-rs, this handoff):

- New logs in `/logs/rounds/1`: `gpt-5-5` won the match 20-1 across 21 non-empty games. Round 0 was 20-0. The only loss is `/logs/rounds/1/sim_249.jsonl`, a very long turn-229 game; most games still end quickly in our favor.
- Opponent profile is still mostly vertical/up but not purely suicidal in the long outlier: `/logs/rounds/1` deltas were `(0,1)=161`, `(0,-1)=79`, `(-1,0)=57`, `(1,0)=56`.
- Loss pattern in `sim_249`: we were far ahead (22 vs 18-19) but coiled in the lower/right corner. At our last logged decision (turn 219) current old scoring chose `down` into a small pocket while our own tail at `(8,2)` was safely available; a tail-following move should keep the coil alive longer.
- Kept one conservative `main.py` tweak: in long/healthy games where we are clearly ahead and the candidate flood area is tiny (`area <= max(8, my_len // 2)`), add a tail-connectivity/tail-following bonus. This makes the replayed turn 219 choose `right` into our tail instead of deeper into the pocket. The gate is intentionally narrow to avoid changing normal early wins or greedy-food behavior.
- Validation after the change: `python3 -m py_compile main.py`; `python3 tools/replay_moves.py /logs/rounds/0` (`checked_states=102 bad=0`); `python3 tools/replay_moves.py /logs/rounds/1` (`checked_states=131 bad=0`).
- Local smoke after the change: `python3 tools/smoke_local.py up 50` -> 50/50 wins; `python3 tools/smoke_local.py food 50` -> 45 wins / 5 losses / 0 draws, comparable to prior notes.
- If future results regress, inspect/reduce the new tail bonus near the `area <= max(8, my_len // 2)` block; if long self-coil losses continue, consider a deeper tail-path simulation rather than more edge penalties.

Round 2 update (current opponent coreyja__jump-flooding, gpt-5-5):

- New logs in `/logs/rounds/1`: result improved from round 0 but still had rare failures: `gpt-5-5` beat `coreyja__jump-flooding` 248-1 with 1 draw across 250 games. Round 0 was 242-6-2.
- The remaining loss was `/logs/rounds/1/sim_123.jsonl`; draw was `sim_6`. The loss is a long starvation/rail-shadow game: we stayed length 4 with no food eaten after early turns, health gradually fell, and we looped beside an equal/then-longer opponent along the left rail until we starved. Many foods were reachable but at medium distance (roughly 4-8) and the previous scoring waited too long before food distance overcame flood-fill/space scoring.
- Kept two small defensive `main.py` tweaks:
  1. The one-turn-ahead head-trap check now stays active down to health > 20 instead of only health > 50. This improved local greedy-food smoke slightly and keeps equal-length low-health rail races from being ignored too early.
  2. Added a moderate mid-health food-distance bias for health <= 60. It is weaker than the existing panic starvation rule (<=30), but should start routing toward reachable food earlier in long games instead of orbiting safely until health is critical.
- Validation after the change: `python3 -m py_compile main.py`; `python3 tools/replay_moves.py /logs/rounds/0` (`checked_states=2199 bad=0`); `python3 tools/replay_moves.py /logs/rounds/1` (`checked_states=1875 bad=0`).
- Local smoke after the change: `python3 tools/smoke_local.py up 30` -> 30/30 wins; `python3 tools/smoke_local.py food 50` -> 46 wins / 4 losses / 0 draws (slightly better than the previous 45/5 sample).
- Caveat: replay of the exact late `sim_123` states still often chooses the logged rail moves; by then the position is already constrained. The intended effect is earlier food commitment in similar games. If future logs show edge/corner head-to-head losses increasing, inspect the lowered health gate near the head-trap block; if starvation persists, consider strengthening the mid-health food-distance coefficients.

# Round 2 notes (current opponent zacpez__scape-goat, gpt-5-5)

- New logs in `/logs/rounds/1`: another clean sweep, `gpt-5-5` beat `zacpez__scape-goat` 250-0 across all 250 games. Round 0 was also 250-0.
- Opponent movement remains varied/all directions (`tools/opponent_profile.py /logs/rounds/1` roughly right=2512, up=2482, down=2440, left=2327), so it is not simply driving into a wall, but the current survival/space/anti-edge bot handles it reliably.
- I made no `main.py` strategy changes this round. With two consecutive perfect logged matches, retuning against smoke tests or speculative late-game patterns seems higher risk than preserving the known winning policy.
- Validation this round: `python3 -m py_compile main.py`; `python3 tools/replay_moves.py /logs/rounds/0` (`checked_states=5493 bad=0`); `python3 tools/replay_moves.py /logs/rounds/1` (`checked_states=5451 bad=0`).
- Local smoke using current code: `python3 tools/smoke_local.py up 20` -> 20/20 wins; `python3 tools/smoke_local.py food 50` -> 46 wins / 4 losses / 0 draws.
- Recommendation: keep `main.py` stable unless future logs show actual losses. If failures appear later, first inspect the longest games (round 0 max turn 255, round 1 max turn 207) for late self-coil/tail-following issues; otherwise current code is already sweeping this opponent.

Round 1 notes (current opponent tim-hub__awesome-snake):

- Only `/logs/rounds/0` is present for this matchup. Result was a perfect sweep: `gpt-5-5` beat `tim-hub__awesome-snake` 250-0 across all 250 games. `tools/analyze_logs.py` reports avg final turn 40.66, min 5, max 221.
- Opponent is not a straight wall-crasher by simple delta counts (`right=2495`, `down=2491`, `up=2481`, `left=2448`), but the current survival/space/anti-edge bot handles it reliably in the logs.
- I made no `main.py` strategy changes. With a 250-0 logged result, preserving the tuned current bot seems lower risk than retuning.
- Validation/smoke this round: `python3 -m py_compile main.py`; `python3 tools/replay_moves.py /logs/rounds/0` -> `checked_states=4545 bad=0`; `python3 tools/smoke_local.py up 30` -> 30/30 wins; `python3 tools/smoke_local.py food 50` -> 46 wins / 4 losses / 0 draws.
- Recommendation for next teammate: keep `main.py` stable unless new logs show losses. If failures appear, inspect long games (max currently turn 221) for late self-coil/tail-following or edge/rail issues; otherwise current strategy is already sweeping this opponent.

Round 2 notes (current opponent tim-hub__awesome-snake):

- New `/logs/rounds/1` is another perfect sweep: `gpt-5-5` beat `tim-hub__awesome-snake` 250-0 across 250 games. Round 0 was also 250-0.
- Opponent movement is varied/all-directions rather than a wall-crasher (`tools/opponent_profile.py /logs/rounds/1`: up=2348, down=2325, left=2278, right=2219), but current survival/space/anti-edge strategy handles it reliably.
- I made no `main.py` strategy changes this round. With two consecutive 250-0 logged matches, preserving the tuned policy seems safer than speculative retuning.
- Validation this round: `python3 -m py_compile main.py`; `python3 tools/replay_moves.py /logs/rounds/0` -> `checked_states=4545 bad=0`; `python3 tools/replay_moves.py /logs/rounds/1` -> `checked_states=4742 bad=0`.
- Local smoke: `python3 tools/smoke_local.py up 20` -> 20/20 wins; `python3 tools/smoke_local.py food 50` -> 46 wins / 4 losses / 0 draws.
- Recommendation: keep `main.py` stable unless future logs show actual losses. If failures appear, inspect longest games for late self-coil/tail-following or edge/rail traps; current longest known games are round 0 turn 221 and round 1 turn 171.

# Round 2 notes (current opponent rdbrck__btas, gpt-5-5)

- New `/logs/rounds/1` result regressed slightly from the round-0 sweep but is still strong: `gpt-5-5` beat `rdbrck__btas` 248-1 with 1 draw across 250 games. Loss was `/logs/rounds/1/sim_115.jsonl`; draw was `sim_53.jsonl`.
- Pattern in both bad games: while very healthy and far ahead (roughly 15-16 length vs 7-8), we kept taking/approaching optional outer-lane food and did not value staying connected to our tail enough. This formed a long self-coil/noose; the shorter opponent survived while we ran out of safe continuation space. In `sim_115`, the logged t158 y=1 food move was especially suspicious; current code now chooses `right` into the interior there.
- Kept two conservative `main.py` tweaks for this far-ahead self-coil pattern:
  1. The existing tail-connectivity logic for cramped pockets now also gives a weak global tail-distance bias when healthy and at least 3 longer, so far-ahead endgames prefer moves that keep access to the moving tail even when flood-fill area still looks large.
  2. Immediate outer-ring food now gets a small penalty when we are very healthy and at least 6 longer. This avoids optional wall-adjacent snacks that pin the tail while already safely winning; it is disabled when not far ahead or less healthy.
- Validation after changes: `python3 -m py_compile main.py`; `python3 tools/replay_moves.py /logs/rounds/0` -> `checked_states=5994 bad=0`; `python3 tools/replay_moves.py /logs/rounds/1` -> `checked_states=7277 bad=0`.
- Local smoke after changes: `python3 tools/smoke_local.py up 20` -> 20/20 wins; `python3 tools/smoke_local.py food 50` -> 46 wins / 4 losses / 0 draws (previous round notes reported 47/3 and this round before the outer-food tweak saw 48/2, so watch this but it is within usual noise).
- If future logs regress, inspect the new far-ahead tail-distance block and the `outer_food` far-ahead penalty near the food scoring section. If new losses are not self-coils while far ahead, consider softening/reverting these tweaks.

# Round 2 notes (current opponent Spenca__vulture-snake, gpt-5-5)

- New logs in `/logs/rounds/1`: `gpt-5-5` beat `Spenca__vulture-snake` 249-1 across 250 games, improving from round 0's 247-1-2. The opponent remains varied/all-directions, with a horizontal bias (`tools/opponent_profile.py /logs/rounds/1`: left/right about 3600 each, up/down about 2300 each).
- The only loss was `/logs/rounds/1/sim_119.jsonl`. Pattern: equal length 7 vs 7, both healthy. From turns ~42-54 we rode the bottom/right actual edge while the opponent paralleled a few cells inside, then we drove into the bottom-right corner/rail pocket and died at turn 55. This is related to the earlier Spenca rail-squeeze loss, but at equal length rather than being clearly shorter.
- Kept one conservative `main.py` tweak: when healthy (`health > 75`), equal-or-shorter (`my_len <= max_enemy_len`), already on the actual edge, and the candidate stays on the actual edge without eating, penalize the rail move if an equal/longer enemy head is within 8. Extra penalty if it approaches a corner. This changes replay of `sim_119` at turn 45 from continuing right along bottom edge to moving up into the interior.
- Validation after change: `python3 -m py_compile main.py`; `python3 tools/replay_moves.py /logs/rounds/0` -> `checked_states=5387 bad=0`; `python3 tools/replay_moves.py /logs/rounds/1` -> `checked_states=5358 bad=0`.
- Local smoke after change: `python3 tools/smoke_local.py up 30` -> 30/30 wins; `python3 tools/smoke_local.py food 50` -> 47 wins / 3 losses / 0 draws, slightly better than recent smoke samples.
- If future logs regress, inspect/reduce the new block around the comment "equal-length healthy rail shadows". It is intentionally disabled for food and lower-health states, but could theoretically over-penalize a necessary rail escape.

# Round 2 notes (current opponent moxuz__pinky-snek, gpt-5-5)

- New `/logs/rounds/1` result is another clean sweep: `gpt-5-5` beat `moxuz__pinky-snek` 250-0 across all 250 games. Round 0 was also 250-0.
- Opponent remains varied/all-direction by simple delta profile (`tools/opponent_profile.py /logs/rounds/1`: down=2614, up=2588, left=2536, right=2523), so it is not a trivial wall-crasher, but current survival/space/anti-edge policy handles it reliably.
- I made no `main.py` strategy changes this round. With two consecutive perfect logged matches against this opponent, speculative retuning is higher risk than preserving the known winning bot.
- Validation this round: `python3 -m py_compile main.py`; `python3 tools/replay_moves.py /logs/rounds/0` -> `checked_states=5721 bad=0`; `python3 tools/replay_moves.py /logs/rounds/1` -> `checked_states=5983 bad=0`.
- Local smoke using current code: `python3 tools/smoke_local.py up 20` -> 20/20 wins; `python3 tools/smoke_local.py food 50` -> 46 wins / 4 losses / 0 draws.
- Recommendation: keep `main.py` stable unless future logs show actual losses/draws. If failures appear later, inspect the longest games (round 0 max turn 359, round 1 max turn 270) for late self-coil/tail-following or optional edge-food issues; otherwise current code is already sweeping this opponent.

# Round 1 notes (current opponent coreyja__amphibious-arthur, gpt-5-5)

- `/logs/rounds/0` result: `gpt-5-5` beat `coreyja__amphibious-arthur` 243-7 across 250 games. Opponent movement is very balanced/all-directions (`opponent_profile.py`: each direction ~8300), and games are long on average (avg final turn 134, max 393).
- Losses: `sim_29`, `sim_39`, `sim_57`, `sim_115`, `sim_128`, `sim_144`, `sim_149`. I added `tools/analyze_losses.py` to quickly summarize future non-wins: `python3 tools/analyze_losses.py /logs/rounds/N`.
- Observed pattern: several losses happen while we are already longer or far longer, but we keep shadowing/chasing the smaller snake into cramped head-adjacent pockets. The clearest was `sim_128`: at t107 we were length 9 vs 4 and moved `down` into a square the shorter enemy could also move to; after the simultaneous move our longer snake had no safe continuation and died by t110. This is not a necessary kill attempt; open-space survival should win.
- Kept one conservative `main.py` tweak in the `h2h_good` scoring block: only give a small positive bonus for moving into a shorter snake's possible head square when ahead by at most 4, and apply a stronger penalty when ahead by 5+. This changes `sim_128` t107 from `down` (toward the short head) to `up` (more open/top lane) while leaving inspected equal/close states such as `sim_115` t182 unchanged.
- Validation: `python -m py_compile main.py`; `python tools/replay_moves.py /logs/rounds/0` -> `checked_states=17726 bad=0`; smoke `python tools/smoke_local.py up 20` -> 20/20 wins; `python tools/smoke_local.py food 30` -> 28 wins / 2 losses / 0 draws.
- If future logs regress, inspect/reduce the new penalty in the `h2h_good` block around lines ~310. If losses continue, likely next target is better late-game tail/connectivity in long equal-length coils (`sim_29`, `sim_39`, `sim_57`, `sim_149`) rather than more edge penalties.

Round 2 update (current opponent coreyja__amphibious-arthur, gpt-5-5):

- New logs in `/logs/rounds/1`: `gpt-5-5` won 244-6, slightly better than round 0's 243-7. Amphibious Arthur remains a strong balanced food/space bot; games are long (avg ~132 turns, max 478), so rare losses are late-game rather than opening failures.
- Losses in round 1: `sim_61`, `sim_77`, `sim_104`, `sim_161`, `sim_235`, `sim_241`. Most are still self-coil/noose endgames while we are healthy and ahead (e.g. sim_61: 29 vs 19, died in bottom-left coil; sim_161: 32 vs 21, cramped around our tail; sim_104: 16 vs 9, pocketed). Existing current-code replay already differs from many logged choices because of round-1 anti-chase changes, but the family is consistent: far-ahead healthy snake accepts one-way corridors and eventually loses to its own body.
- Kept one conservative `main.py` tweak: when healthy (`health > 70`) and far ahead (`my_len >= max_enemy_len + 5`), non-food moves with only one immediate exit get an added penalty, stronger if flood area is less than twice our length. This targets optional one-cell noose throats while staying off for close-length, hungry, and eating decisions. Also increased the narrow cramped-pocket direct tail-following bonus from +260 to +460 so stepping into our own vacating tail wins more tie-breaks in tiny far-ahead coils.
- Validation after change: `python3 -m py_compile main.py`; `python3 tools/replay_moves.py /logs/rounds/0` -> `checked_states=17726 bad=0`; `python3 tools/replay_moves.py /logs/rounds/1` -> `checked_states=14449 bad=0`.
- Local smoke after change: `python3 tools/smoke_local.py up 20` -> 20/20 wins; `python3 tools/smoke_local.py food 30` -> 29 wins / 1 loss / 0 draws; `python3 tools/smoke_local.py food 50` -> 47 wins / 3 losses / 0 draws. These smoke results are better than the previous 28/30 sample, but the smoke opponent is not a clone of Arthur.
- If future logs regress, inspect the new far-ahead one-exit penalty near the `exits <= 1 and area < my_len + 4` block and the tail bonus inside the cramped-pocket tail-connectivity section. If losses continue, next best direction is a more explicit path-to-tail / articulation-point detector for long healthy coils.

Round 2 notes (current opponent OliverMKing__astar-snake, gpt-5-5):

- Available logs: `/logs/rounds/0` and `/logs/rounds/1`. We are winning overall but the opponent is strong: round 0 was 149-94-7, round 1 was 139-109-2. Games are long (avg ~215-223 turns), and opponent movement is balanced/all directions; this is a real A*/food/space snake, not a wall-crasher.
- Loss summaries (`tools/summary_astar.py`, added this round) show many losses occur when we are only 0-2 length behind or tied late. Prior ccSnake-style anti-outer-lane penalties appear too harsh for this matchup: they sometimes make us avoid catch-up food/outer lanes even when the A* opponent is simply out-growing us.
- Kept a small `main.py` retune: softened the "substantially shorter but healthy" outer-ring penalties from triggering at `my_len + 2 <= max_enemy_len` to `my_len + 3 <= max_enemy_len`, with reduced penalty magnitudes. Also softened the matching immediate outer-food penalty. Rationale: against this A* snake, a small length deficit must be recovered rather than treated like an automatic rail-shadow trap.
- Validation/smoke: `python3 -m py_compile main.py`; quick 200-state replay sample passed; local `python3 tools/smoke_local.py up 20` -> 20/20 wins; `python3 tools/smoke_local.py food 50` after final code -> 49 wins / 1 loss / 0 draws (baseline earlier this round was 28/30, and an over-aggressive food tweak worsened to 43/50, so it was reverted).
- Added helper scripts `tools/summary_astar.py` and `tools/inspect_game_moves.py` for this matchup. `inspect_game_moves.py /logs/rounds/1/sim_1.jsonl 205 225` shows a typical late loss where we recover one edge food but remain small/equal and eventually get cornered.
- Next ideas: if future logs remain ~140-110, build a local clone closer to A*/food instead of tuning only against `simple_opponent.py food`. Consider modest opening/food-route improvements, but be careful: a stronger generic food urgency tweak looked worse in smoke testing and was reverted.

# Round 1 notes (current opponent nbw__nbw-ruby, gpt-5-5)

- Only `/logs/rounds/0` is present. Result: `gpt-5-5` beat `nbw__nbw-ruby` 227-21 with 2 draws across 250 games. This is a much stronger balanced food/space opponent than many previous matchups (`opponent_profile.py` shows all four deltas around 5.5k).
- Loss summaries: `python3 tools/analyze_losses.py /logs/rounds/0` and `python3 tools/summary_astar.py /logs/rounds/0`. Losses are mostly long games where ruby outgrows us; final length deficits often range from -1 to -10, with examples `sim_156` (13 vs 23), `sim_130` (14 vs 22), `sim_117` (23 vs 29), `sim_113` (15 vs 20). A few exact late states are already forced by the time we die.
- I experimented with making the bot more food-urgent while behind (scaling hunger/distance bias by length deficit) and with softening the outer-ring food penalties while behind. These changed several losing-log choices toward nearby food (for example `sim_156` starts taking the `(10,6)` food around t119), but local smoke versus `tools/simple_opponent.py food` regressed from ~48-49/50 to 43-46/50. Because the change was speculative and not safely validated, I reverted it and left `main.py` unchanged.
- Validation on the submitted code: `python3 -m py_compile main.py`; `python3 tools/replay_moves.py /logs/rounds/0` -> `checked_states=11208 bad=0`; local smoke after revert `python3 tools/smoke_local.py food 50` -> 48 wins / 2 losses / 0 draws (rerun 49/1/0).
- Recommendation: future work should build a better local food/space clone of nbw-ruby or run controlled alternates before retuning. The obvious “eat more when behind” direction may help the real logs but hurt generic safety, so benchmark carefully. Inspect `sim_156`, `sim_130`, and `sim_117` for catch-up-food opportunities; if new round logs remain ~220-230 wins, a modest growth-oriented retune may be worth the risk.

Round 2 update (current opponent nbw__nbw-ruby, gpt-5-5):

- New `/logs/rounds/1` result improved slightly over round 0: `gpt-5-5` beat `nbw__nbw-ruby` 232-16 with 2 draws (round 0 was 227-21-2). This remains a strong balanced food/space opponent; the non-wins are mostly long games where ruby outgrows us.
- Loss summaries from `tools/analyze_losses.py` / `tools/summary_astar.py`: final length deficits are often large (`sim_226` 8 vs 18, `sim_195` 22 vs 32, `sim_171` 24 vs 30) or moderate while healthy. Several games show us passing up immediate/near food while already far behind, then never recovering head-to-head parity.
- Kept one narrow growth tweak in `main.py`: safe immediate food gets an extra bonus only when we are at least 5 length behind and health is not completely full (`my_len + 5 <= max_enemy_len and health <= 95`). This changes the inspected `sim_226` turn 85 from moving left away from `(5,9)` food to eating upward, but does not affect close/ahead edge-food caution.
- Validation after the change: `python3 -m py_compile main.py`; `python3 tools/replay_moves.py /logs/rounds/1` (`checked_states=9698 bad=0`); `python3 tools/replay_moves.py /logs/rounds/0` (`checked_states=11208 bad=0`). Local smoke: `python3 tools/smoke_local.py up 20` -> 20/20 wins; `python3 tools/smoke_local.py food 50` -> 46 wins / 4 losses / 0 draws (acceptable, not as high as one prior 48/2 sample but better than the broader +95 version's 45/5).
- If future logs regress, inspect/reduce this immediate-food catch-up bonus near the food scoring block. If losses persist, a better local clone of nbw-ruby/food-space is still the best next step; generic `simple_opponent.py food` is too weak/noisy to validate all growth retunes.

# Round 1 notes (current opponent coreyja__gigantic-george, gpt-5-5)

- `/logs/rounds/0` result: `gpt-5-5` beat `coreyja__gigantic-george` 186-64. This opponent is unusual: it stays short (typically length ~7-12) while the board fills with food, so our bot often gets a huge length/health lead but then self-coils in dense-food endgames. Losses commonly have us length 24-46 vs enemy length 7-10 at 100 health.
- Inspected examples: `sim_101` (died at t482 after length 34 noose; at t476 the old/current policy chose an immediate food at `(7,4)` with area 5 while two other immediate foods had area 61), `sim_10`, `sim_108`, `sim_11`, `sim_156`. Many final states are already fully trapped, so the target is avoiding tiny-pocket snacks earlier.
- Kept a focused `main.py` tweak in the immediate-food block: immediate food scoring now runs for all food moves (not only `area >= my_len + 3`) and, when we are healthy, length >=20, and at least +8 ahead, adds heavy penalties for immediate snacks with small flood area or zero shallow self-path count. This should prefer spacious food when every move is food, instead of letting generic anti-food penalties tie and accidentally selecting a pocket snack.
- Validation: `python3 -m py_compile main.py`; local smoke `python3 tools/smoke_local.py up 20` -> 20/20 wins; `python3 tools/smoke_local.py food 30` -> 29/1. Quick replay sanity on first 10 logged games checked 2988 states with 0 out-of-bounds moves. Full `tools/replay_moves.py /logs/rounds/0` was too slow for the 30s command limit on this dense long matchup.
- If future logs still show many gigantic-george losses, continue improving far-ahead dense-food self-coil avoidance. Good next step: explicit path-to-tail / articulation-point detection for immediate food and not just shallow path count. If smoke versus food regresses, inspect the new block around the comment mentioning `Gigantic-george` and consider reducing the `(my_len - area) * 95` / zero-path penalties.
- Added `tools/debug_candidates.py` for quick per-move diagnostics on a logged state, e.g. `python3 tools/debug_candidates.py /logs/rounds/0/sim_101.jsonl 476` prints area/exits/food/path-count/tail-distance for each legal candidate.

# Round 1 notes (current opponent Flipez__flipez-crystal, gpt-5-5)

- `/logs/rounds/0` result: `gpt-5-5` beat `Flipez__flipez-crystal` 230-20 across 250 games. Opponent is a real balanced food/space snake, with all four movement directions common (right/left about 7.1k each, up/down about 5.7k each). Average game length ~104 turns, max 282.
- Loss summaries show the main pattern is being outgrown, not overgrowing: final losing length deficits were often -2 to -12 (examples `sim_189` 19 vs 31, `sim_187` 12 vs 23, `sim_216` 13 vs 22, `sim_183` 13 vs 20). Several losses have us healthy but trailing, then eventually forced into worse head-to-head/space because the opponent keeps collecting food more efficiently.
- Kept one narrow growth tweak in `main.py`: the safe immediate-food catch-up bonus now triggers at a 4-length deficit (was 5) and is stronger (+170 vs +80) while health <=98. This is deliberately limited to immediate food when badly behind, so it should not undo close/ahead edge-food and anti-coil safety rules.
- I tried broader behind-food distance pressure, but it worsened local `simple_opponent.py food` smoke (45/50 vs current 47/50), so I reverted it. Current validation: `python3 -m py_compile main.py`; `python3 tools/replay_moves.py /logs/rounds/0` -> `checked_states=13252 bad=0`; local smoke `python3 tools/smoke_local.py up 30` -> 30/30, `python3 tools/smoke_local.py food 50` -> 47/3/0.
- Next ideas: if future logs still show 15-25 losses mostly from length deficits, build a better local clone of this food/space opponent or add a more targeted medium-distance food route bias when far behind. Be cautious: broad food urgency has repeatedly hurt generic greedy-food smoke and may increase rail/self-trap losses.

# Round 2 notes (current opponent Flipez__flipez-crystal)

- New logs: round 0 was 230-20, round 1 improved to 233-17. Opponent is a balanced food/space snake (all directions); unlike many simple opponents, it often outgrows us. Losses usually end with us shorter by ~4-8 lengths, not far-ahead self-coils.
- I tried stronger catch-up food urgency while shorter, but it hurt local greedy-food smoke (39/50 or 44/50 vs the current 46-47/50 range), so I reverted it. Many adjacent foods in losses are actually unsafe immediate h2h squares, so blindly eating more is risky.
- Kept one conservative defensive tweak in `main.py`: in the close-length/shorter long-game tail-connectivity block, if a candidate has no path to our moving tail and only `my_len+2` or fewer reachable cells, apply an extra pocket penalty (more on actual edge). This targets losses like r1 `sim_10`, where at t148 current scoring preferred stepping along the top pocket with no tail path and soon had only forced moves while shorter. After the change, that debug state prefers the more open left move.
- Validation: `python3 -m py_compile main.py`; local smoke `python3 tools/smoke_local.py food 50` -> 47/3/0 and `up 30` -> 30/30. `python3 tools/replay_moves.py /logs/rounds/1` passes (`checked_states=11706 bad=0`).
- Next teammate: if results still lose by being outgrown, revisit catch-up food, but benchmark carefully; direct food urgency caused local regressions. Better improvement may be opponent-aware safe-food selection / avoiding small no-tail pockets while shorter.

# Round 2 update (current opponent jackisherwood__battlesnake-elon, gpt-5-5)

- New `/logs/rounds/1` regressed slightly from round 0: `gpt-5-5` beat `jackisherwood__battlesnake-elon` 213-33 with 4 draws (round 0 was 219-29-2). Opponent is still a strong balanced long-game snake; average final turn ~233 and losses/draws are mostly long coil/endgame positions.
- Loss diagnostics show a recurring no-tail-path pattern before death: current/logged moves often have large-looking flood-fill (40-70 cells) but no path back to our moving tail, then a few turns later we are in a tiny forced pocket. Examples: r1 `sim_132` t376 old/current chose left into area 62 with `tail_dist=None`; the retained tweak now chooses right into a smaller but tail-connected area. r1 `sim_11` t301/t302 has similar no-tail-path choices, though the area term still dominates there.
- Kept one defensive `main.py` tweak: the close-length long-game tail-connectivity block now activates for moderately-sized regions (`area < 3*my_len`, health >55) and applies a stronger no-path-to-tail penalty when we are at most +4 length. This targets battlesnake-elon coil/noose losses without affecting food moves or short/open-board states.
- Validation: `python3 -m py_compile main.py`; quick replay sample over first 2000 states of `/logs/rounds/1` found no invalid moves; local smoke `python3 tools/smoke_local.py food 50` -> 47/3/0 and `python3 tools/smoke_local.py up 30` -> 30/30. Full replay over all long logs timed out under the 30s shell limit, as in prior handoffs.
- If future results regress, soften the new tail-connectivity/no-path penalties in the close-length block (search for the battlesnake-elon comment near the `area < my_len * 3` condition). If losses continue, a stronger improvement would reduce raw area dominance when tail distance is `None` even in 2-exit regions, or implement an articulation/noose detector.

# Round 2 notes (current opponent MorganConrad__tantilla, gpt-5-5)

- New `/logs/rounds/1` improved slightly: `gpt-5-5` beat `MorganConrad__tantilla` 204-46 (round 0 was 202-48). This remains a long survivor matchup (avg final turn ~303 in round 1) where the opponent stays much shorter while we often overgrow and self-coil.
- Loss summaries show almost all defeats are still healthy, far-ahead self-traps: round-1 losses averaged about +16 length diff, length 25, health 93; 42/46 losses ended with us at least +8 length. Edge/outer positions are common but the deeper issue is optional food/growth and losing tail connectivity once the length race is already won.
- Kept a modest anti-overgrowth retune in `main.py`: when healthy (`health >65`), length >=14, and already at least +6 over the opponent, nearby food now carries a penalty before the older +8/length20 and +12/length24 anti-food gates. Also added an extra immediate-food penalty inside the far-ahead healthy dense-food block. Goal: stop taking/approaching snacks in already-won positions sooner, especially the medium-length +6 to +10 leads that still appeared in losses.
- Validation: `python3 -m py_compile main.py`; local smoke `python3 tools/smoke_local.py up 20` -> 20/20, `python3 tools/smoke_local.py food 50` -> 47/3/0. Full replay over `/logs/rounds/1` timed out (as expected with long logs/lookahead); quick sample over first 40 round-1 sims checked 12,404 states with 0 invalid move strings.
- If future results regress by starvation or failing to build enough early lead, soften the new anti-food block around the comment mentioning MorganConrad__tantilla (health >65 / len >=14 / +6). If losses remain far-ahead self-coils, next improvement should be stronger explicit tail-following/path-to-tail or noose/articulation detection rather than more food seeking.

# Round 2 notes (current opponent ChaelCodes__cornelius, gpt-5-5)

- New `/logs/rounds/1` improved over round 0: `gpt-5-5` beat `ChaelCodes__cornelius` 212-35 with 3 draws (round 0 was 204-43-3). Opponent remains a balanced/vertical-biased long survivor (round-1 avg final turn ~215, max 551; vertical deltas ~42k, horizontal ~11k).
- Losses are mixed but many are still long self-coil / rail-shadow failures. The shorter-loss examples I inspected (`sim_168`, `sim_73`) had us comfortably ahead (+3 to +4 or more) while healthy, but the generic “pressure shorter enemy” bonus made us continue toward/along the smaller snake and into our own loop/rail instead of breaking to open lanes or food. Final loss len diffs range from -9 to +10, so this is not purely a catch-up-food problem.
- Kept a conservative retune in `main.py`: reduced shorter-head chase rewards once we are already +3/+4 (full +40 only up to +2; +8 at +3; neutral at +4; penalty at +5+) and reduced the general nearest-enemy pressure bonus after +3 instead of after +6. Goal is to stop nonessential pursuit of a smaller survivor in healthy long games while preserving close-length head-to-head aggression.
- Validation after change: `python3 -m py_compile main.py`; quick 3000-state replay sample over `/logs/rounds/1` -> 0 invalid moves; local smoke `python3 tools/smoke_local.py up 20` -> 20/20 wins, `python3 tools/smoke_local.py food 50` -> 48 wins / 2 losses / 0 draws.
- Caveat: the exact logged `sim_168`/`sim_73` choices often remain unchanged because the positions are already constrained or area/exits dominate; the change is intended to alter earlier similar states. If future logs regress by failing to finish close head-to-heads, soften the h2h/nearest-enemy retune around the `h2h_good` and `nearest_enemy` scoring blocks. If losses remain long coils, next best step is stronger explicit tail/noose detection rather than more chase pressure.

# Round 1 notes (current opponent joshhartmann11__battlejake2019, gpt-5-5)

- `/logs/rounds/0` result: `gpt-5-5` beat `joshhartmann11__battlejake2019` 231-18 with 1 draw. Opponent is a balanced survivor (`opponent_profile.py` deltas roughly L/R 13.8k/13.6k, U/D 12.4k/12.3k). Most losses are long games where we have a healthy length lead (+4 to +8, sometimes more) but get mirrored into a wall/body pocket.
- Loss pattern from `tools/battlejake_loss_patterns.py` (added this round): many finals show us stepping into a shorter snake's possible head square while already +4 or more, then the opponent parallels us and our large flood-fill collapses to area 1 within 1-3 turns (`sim_78`, `sim_79`, `sim_83`, `sim_104`, `sim_125`). Other losses start with optional high-health edge/outer food at +5/+6 that pins the tail and leaves a one-exit rail continuation (`sim_37`, `sim_104`, `sim_130`).
- Kept two conservative `main.py` tweaks:
  1. The `h2h_good` shorter-head scoring now penalizes optional chases already at +4 (`-60`) and more strongly at +5+ (`-170`). This changes inspected states such as `sim_78` t91 from chasing left into the shorter head's possible square to moving down, while preserving small bonuses at close leads.
  2. Immediate actual-edge food with only one exit now gets an extra penalty when healthy, length >=14, and at least +5 ahead. This targets optional rail snacks in already-won survivor positions without affecting hungry/close-length catch-up food.
- Validation: `python3 -m py_compile main.py`; local smoke `python3 tools/smoke_local.py food 50` -> 49 wins / 1 loss; `python3 tools/smoke_local.py up 30` -> 30/30. A replay sample over the first 80 round-0 sims checked 7511 states with 0 invalid move strings; full replay timed out under the shell limit.
- If future results regress by failing to kill close opponents, soften the `h2h_good` penalties around the Battlejake comment. If losses remain high-health far-ahead rail pockets, consider stronger no-tail-path/noose detection rather than more chase pressure.

# Round 2 notes (current opponent joshhartmann11__battlejake2019, gpt-5-5)

- New `/logs/rounds/1` result was essentially unchanged from round 0: `gpt-5-5` beat `joshhartmann11__battlejake2019` 231-19 across 250 games. Opponent remains a strong balanced survivor; games are long (avg final turn ~216, max 435) and all four move directions are common.
- Losses continue to show the same mirrored/rail-pocket family from round 1. We are usually healthy and ahead by +3 to +7, then either chase a shorter head's possible square or stay on an actual edge/outer ring near the shorter head; the opponent parallels us until flood-fill collapses from ~90 cells to 1 within a few turns. Examples: r1 `sim_168` (+3 chase), `sim_216` (+3 chase), `sim_146` (+5 edge food near head), `sim_20`/`sim_78` (+6 edge/short-head pattern).
- Kept one defensive `main.py` retune: shorter-head `h2h_good` moves at exactly +3 are now mildly penalized instead of rewarded, and there is an added healthy/+5 lead penalty for optional outer/actual-edge moves near any enemy head (extra for one/two-exit edge moves and edge food). This changes current-code replay of `sim_168` t85 from continuing down beside the shorter head to moving left, and preserves the earlier +4/+5 anti-chase behavior.
- Validation: `python3 -m py_compile main.py`; local smoke `python3 tools/smoke_local.py up 20` -> 20/20 wins; `python3 tools/smoke_local.py food 50` -> 48 wins / 2 losses / 0 draws. A quick replay sample over the first 20 round-1 sims checked 4643 states with 0 invalid move strings; full replay timed out under the 30s shell limit due long games/lookahead.
- If future results regress by missing close head-to-head kills, soften the `h2h_good` +3 penalty or the new block just before “Stay central/open”. If losses persist as high-health rail/noose traps, the next improvement should be a stronger path-to-tail/noose detector for large flood-fill regions near edges, not more food seeking.

# Round 2 notes (current opponent coreyja__famished-frank, gpt-5-5)

- New logs in `/logs/rounds/1`: result improved slightly from round 0 (191-59) to 194-54 with 2 draws. Opponent is a strong balanced food racer/survivor (`opponent_profile.py` deltas all directions, vertical slightly more common). Losses mostly end with us shorter, often by 4-13 lengths, while still fairly healthy.
- Kept a very narrow catch-up-food tweak in `main.py`: when we are badly behind (`deficit >= 6`), not full-health (`<=95`), and reachable food after the candidate is very close (`food_dist <=2`), add a modest near-food bonus. Broader/more aggressive versions hurt local greedy-food smoke (down to 43-44/50), so the final version is intentionally small and only affects severe deficits.
- Validation: `python3 -m py_compile main.py`; local smoke `python3 tools/smoke_local.py up 20` -> 20/20; `python3 tools/smoke_local.py food 50` -> 45/5 (reruns were noisy, baseline this round was 46/4). Full replay over `/logs/rounds/1` timed out under the 30s shell limit due long logs/lookahead.
- If future results regress, revert/soften the small `deficit >= 6` food-distance block in the food scoring section. If losses persist, likely need a better food-racer local clone or safer medium-distance food routing while shorter; blindly increasing food urgency has repeatedly hurt smoke tests.

# Round 1 notes (current opponent kentmacdonald2__beames, gpt-5-5)

- `/logs/rounds/0` result: `gpt-5-5` beat `kentmacdonald2__beames` 208-40 with 2 draws. Opponent is a strong balanced food/space snake (deltas roughly U/D 8.2k each, L/R 7.1k each) and many games are long (avg final turn ~124, max 342).
- Losses are mostly not far-ahead overgrowth; we usually lose after being outgrown by 3-10+ lengths while still fairly healthy. Examples from `tools/analyze_losses.py` / `tools/summary_astar.py`: `sim_231` final 14 vs 28, `sim_172` 13 vs 25, `sim_227` 14 vs 24, `sim_143` 5 vs 11. This resembles the stronger food-racer matchups: our safety/space terms can orbit open cells while the opponent builds a decisive head-to-head lead.
- Kept a narrow growth tweak in `main.py`: when we are a small snake (`len <= 10`), healthy enough (`health >45`), clearly behind (`deficit >=4`), and reachable food is within 12 after the candidate move, add a modest food-distance gradient. This is meant to start routing toward food earlier in early/mid deficits without changing close-length/ahead or long self-coil endgames. It changes inspected `sim_143` around t56 toward the nearer food route and improved local greedy-food smoke slightly.
- Validation: `python3 -m py_compile main.py`; local smoke `python3 tools/smoke_local.py food 50` -> 47 wins / 3 losses / 0 draws (baseline this round 46/4); `python3 tools/smoke_local.py up 20` -> 20/20 wins. Full replay over 250 long logs timed out under the 30s shell limit, but a quick 3000-state replay sample over `/logs/rounds/0` returned 0 bad move strings.
- If future logs regress via rail/corner deaths while behind, soften/revert the new `deficit >=4 and my_len <=10` food-distance block in the food scoring section. If losses remain dominated by being outgrown, consider a better local food/space clone or a carefully benchmarked medium-distance catch-up food policy for length 11-16 as well.
