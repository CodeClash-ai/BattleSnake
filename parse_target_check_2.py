# Let's see the details of move ranking at Turn 138
# Head is at (5, 5).
# Up: (5, 6) -> space = 5, dist to (6, 2) is |5-6| + |6-2| = 1 + 4 = 5.
# Down: (5, 4) -> space = 1, dist to (6, 2) is |5-6| + |4-2| = 1 + 2 = 3.
#
# Our snake length at turn 138 was 24.
# min_space_needed = min(24, 15) = 15.
# Let's check:
# For up: space = 5 < 15, so has_enough_space = 0.
# For down: space = 1 < 15, so has_enough_space = 0.
#
# Since both have has_enough_space = 0, the rank_move function returned:
# For up: (0, 5, -5)
# For down: (0, 3, -1)
#
# Since we sorted by:
# rank_move(item) -> (-has_enough_space, dist, -space)
# Up's key: (0, 5, -5)
# Down's key: (0, 3, -1)
# Down was sorted BEFORE Up because 3 < 5 (dist is the secondary key, lower is better)!
#
# Oh my god! This is a massive bug!
# If neither move has "enough" space, we prioritized the one closer to the food target instead of maximizing space!
# If we don't have enough space, we MUST maximize the space available! Distance to target should be completely secondary or ignored if we are in danger of suffocating!
# Actually, even if space is not "enough", we should STILL prioritize space over distance!
# Wait! Let's think:
# If space < min_space_needed:
# We should sort primarily by space descending!
# Let's look at the ranking function:
# If space >= min_space_needed: we have "enough" space.
# If both have enough space, we can sort by distance to target, then space as a tie-breaker.
# But if space < min_space_needed, we are trapped or in a tight spot, so we MUST prioritize space first, and only use distance as a tie-breaker!
# Let's design a better ranking key!
