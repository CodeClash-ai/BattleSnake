import json

# Let's inspect options and scores for Turn 92 in sim_123.
# At Turn 92, head was at (3, 9).
# Options from (3, 9):
# (3, 10) -> free
# (2, 9) -> occupied
# (4, 9) -> occupied
# (3, 8) -> occupied
# So at Turn 92, (3, 10) was the ONLY available option!
# At Turn 91, head was at (2, 9).
# Options:
# (1, 9) -> occupied
# (3, 9) -> free
# (2, 8) -> occupied
# (2, 10) -> free.
# Let's see: from (2, 9) we could have gone to (3, 9) or (2, 10). We went to (3, 9).
# If we went to (2, 10) at Turn 91, would we be trapped?
# Let's think: on Turn 91, body was [ (2, 9), (1, 9), (0, 9), (0, 8), (1, 8), (2, 8), (3, 8), (4, 8), (4, 9), (4, 10), (5, 10), (6, 10) ]
# If we went to (2, 10) instead of (3, 9):
# Head is at (2, 10). Options: (1, 10), (3, 10).
# From (1, 10): options (0, 10) which is a dead end because (0, 9) and (1, 9) are blocked.
# From (3, 10): options (3, 9) - blocked, (4, 10) - blocked.
# So the whole upper-left area (x <= 4, y >= 8) was a trap because we coiled inside it!
# Wait, why did we enter this region in the first place?
# On Turn 84, head was at (4, 8).
# Body was [ (4, 8), (4, 9), (4, 10), (5, 10), (6, 10), (7, 10), (8, 10), (8, 9), (7, 9), (7, 8), (7, 7) ]
# From (4, 8), options:
# (3, 8) -> free
# (5, 8) -> free
# (4, 7) -> free
# (4, 9) -> occupied
# We chose to go to (3, 8), entering the pocket, instead of (5, 8) or (4, 7).
# Wait! Let's check why we entered (3, 8).
# Let's write a quick simulator test for this scenario or inspect our weights.
# The space inside the pocket was small, but maybe our tail reachability bonus didn't penalize it because tail was reachable?
# Wait! On Turn 84, our tail was at (7, 7).
# If we enter (3, 8), is (7, 7) reachable?
# Yes, because the pocket wasn't fully closed. But we got trapped as we moved deeper.
# Let's look at tail reachability.
# Our tail moves every turn. But if we grow (by eating food), the tail does NOT move (it stays in place).
# Wait, did we eat food?
# On Turn 74 in sim_158:
# Snake gemini-3-5-flash: head={'x': 10, 'y': 10}, body=[..., {'x': 9, 'y': 3}, {'x': 9, 'y': 3}] (length 12, grew because of eating food).
# When we eat food, the tail doesn't move.
# But more importantly, the flood fill doesn't look at "how many moves until tail is gone" or "can we reach the empty space behind our body as it moves".
# Actually, our flood fill treats all body segments as solid obstacles.
# But standard Battlesnake strategy says: a body segment is NOT a permanent obstacle. It moves!
# If we are at head pos and have length L, the body segments will disappear in 1, 2, ..., L turns.
# In our `move` function, we have:
# "Build set of obstacles (all snake body segments, except their tails if they are not growing...)"
# But wait, in our code:
# obstacles = set()
# for snake in board["snakes"]:
#     for seg in snake["body"]:
#         obstacles.add((seg["x"], seg["y"]))
#
# We treat the ENTIRE body as solid obstacles!
# This means we don't realize we can follow our own tail!
# Wait, we do have a "Tail reachability bonus":
# my_tail = (you["body"][-1]["x"], you["body"][-1]["y"])
# obstacles_without_tail = obstacles.copy()
# if my_tail in obstacles_without_tail:
#     obstacles_without_tail.remove(my_tail)
#
# But we ONLY remove the very last segment (the tail)! All other body segments are still treated as solid obstacles!
# If we are length 22, the segments near our tail will also disappear very soon.
# If we do a flood fill, treating body segments as permanent obstacles makes us underestimate the space available to us, OR we might think we can reach our tail, but we don't realize we can also move into the space of body[-2] on the next turn, body[-3] on the turn after, etc.
# Actually, if we follow our own tail, we are safe.
# But if we coil in a tight space where the total volume of the pocket is less than our body length, we are guaranteed to collide with ourselves if we cannot exit.
# Wait! If the pocket has size 10, and we are length 22, and we enter it, we MUST collide with ourselves or the wall because we cannot fit our entire body in it.
# Even if the tail is reachable, we will trap ourselves if the pocket size is smaller than our length!
# In our score:
# if space < my_length:
#     score -= 50000
# Here, `space` is the flood-fill space.
# But wait! On Turn 84, from (4, 8), if we move to (3, 8), what was the `space`?
# The pocket was:
# x from 0 to 3, y from 8 to 10 (size 4 * 3 = 12).
# Plus we could also go down to y <= 7?
# Wait! On Turn 84, y <= 7 was open!
# So the flood fill from (3, 8) could go down to (3, 7), (2, 7), etc., which was completely open board!
# So `space` was very large (almost the whole board).
# But wait, if we go to (3, 8), we are moving into a dead-end corridor/pocket of width 4, and the only exit is (4, 8) or down.
# Wait, if y <= 7 was open, why did we get trapped?
# Because we kept moving deeper into the pocket (to (2, 8), (1, 8), (0, 8), (0, 9), etc.) instead of going down or out!
# Why did we go deeper?
# Let's check:
# Turn 87: head=(1, 8). We went to (0, 8) on Turn 88.
# On Turn 88: head=(0, 8). We went to (0, 9) on Turn 89.
# From (0, 8), could we go to (0, 7)?
# On Turn 88, was (0, 7) free?
# Let's check:
# Turn 88 body: [ (0, 8), (1, 8), (2, 8), (3, 8), (4, 8), ... ]
# If we were at (0, 8), the options were:
# (0, 9) -> free
# (1, 8) -> occupied by body
# (0, 7) -> free
# (-1, 8) -> out of bounds
# So we had (0, 9) and (0, 7) as options!
# Why did we choose (0, 9) instead of (0, 7)?
# Let's check if there was food at y=10 or something.
# On Turn 88, food was at: `[{'x': 0, 'y': 7}, {'x': 0, 'y': 0}, {'x': 8, 'y': 10}]`
# Wait! Food was at (0, 7)!
# If food was at (0, 7), and we were at (0, 8), why did we choose (0, 9) instead of (0, 7)?
# Let's calculate the distance to target.
# If target was (0, 7) (the nearest food), then moving to (0, 7) would make distance 0.
# Moving to (0, 9) would make distance 2.
# So why did we choose (0, 9)?
# Let's check the flood fill space and tail reachability for (0, 7) vs (0, 9).
# If we move to (0, 7):
# (0, 7) is adjacent to the opponent? Or maybe (0, 7) was occupied by opponent head?
# Let's check Turn 88 opponent:
# Oh! Opponent head was not near.
# Let's check the score for (0, 7).
# If we move to (0, 7), what is our flood fill space?
# Wait! Our body is [ (0, 8), (1, 8), (2, 8), (3, 8), (4, 8), (4, 9), (4, 10), ... ]
# This body forms a horizontal wall at y=8 from x=0 to 4.
# So if we are at (0, 8), moving to (0, 7) puts us below the wall.
# If we are below the wall, what is the space? The entire bottom half of the board! Which is huge.
# If we move to (0, 9), we are above the wall (in the pocket).
# The pocket is x from 0 to 3, y from 9 to 10.
# The size of this pocket is only 8 squares!
# So `space` for (0, 9) is at most 8.
# `space` for (0, 7) is at least 50.
# And yet, we chose (0, 9) over (0, 7)?!
# How is that possible?
# Ah! Let's look at the "Tail reachability bonus".
# If we move to (0, 7), is our tail reachable?
# Our tail was at (8, 9).
# Can we reach (8, 9) from (0, 7)?
# Let's see: from (0, 7), we can go right, but our body blockages might prevent us from reaching (8, 9).
# If we move to (0, 9), is our tail reachable?
# Yes, because our body was coiling and the tail was at (8, 9), which might be reachable through the pocket?
# Wait, if tail is reachable from (0, 9) but NOT from (0, 7), then:
# (0, 9) gets +100000 bonus.
# (0, 7) gets 0 bonus.
# Since the tail reachability bonus is 100,000, it completely dominates the 1,000 * space score!
# That is a massive bug!
# The tail reachability bonus is so high (100,000) that it forces the snake to make moves that have tiny space (like 8) just because the tail is reachable, while rejecting a move with huge space (like 50) where the tail is not immediately reachable!
# But wait! If we have 50 space, we don't need to reach our tail right now! We have plenty of room to live and wait for the body to clear.
# Having 100,000 bonus for tail reachability completely breaks the safety heuristic.
# Let's design a much smarter heuristic.
# What is the actual definition of safe space?
# Instead of a binary "tail reachable", we should compute the actual reachable space, taking into account the time it takes for body segments to disappear.
# This is called "Long-term Prediction Flood Fill" or "Time-Aware Flood Fill".
# In a Time-Aware BFS:
# Each node in the BFS has a `time` (or `depth`).
# A cell is blocked at time `t` if there is a snake segment that will still be there at time `t`.
# Let's calculate exactly when each cell becomes free:
# For each snake, its body segments are `body[0], body[1], ..., body[N-1]`.
# Segment `body[i]` will disappear at turn `current_turn + (N - i)`.
# So the cell `(x, y)` will become free at `current_turn + (N - i)` (assuming the snake doesn't grow and cover it again).
# Let's write a highly accurate Time-Aware Flood Fill!
# With a Time-Aware Flood Fill, the reachable space count is extremely precise and naturally understands following tails, coiling, and pocket sizes perfectly!
# Let's write this!
# Let's define the time a cell becomes free:
# For each cell on the board, we can store `free_at_step`.
# By default, empty cells have `free_at_step = 0`.
# For a snake with body segments `[b_0, b_1, ..., b_{N-1}]`:
# `b_i` is at `(x, y)`. It will disappear after `N - i` steps.
# So `free_at_step[(x,y)] = max(free_at_step[(x,y)], N - i)`.
# Wait, if the snake eats food, its length increases by 1, so the tail doesn't move. To be safe, we can assume the snake might grow, or just use `N - i` as a very good approximation.
# In our BFS from start position at step 1:
# We can move to a neighbor `(nx, ny)` at step `s` if `s >= free_at_step[(nx, ny)]`.
# This is beautiful and extremely simple to implement!
# Let's double check this logic:
# If our head is at (1, 1) and tail is at (1, 2) (body length 3: `[(1,1), (1,2), (1,2)]` or `[(1,1), (1,2)]`).
# If we move to (1, 2) at step 1:
# `free_at_step[(1,2)]` for the tail segment is 1 (since it's the last segment).
# Since our step `s` is 1, and `1 >= 1`, we can move there!
# This perfectly allows following our own tail or opponent's tail!
# Let's implement this Time-Aware BFS.
# Let's write a python test script to verify this.
