# Let's see how rank_move works when both space is 5 and can_reach_tail is False.
dist_to_target_8_1 = 10
dist_to_target_9_2 = 10 # let's say

def rank_move(item):
    d, space, can_reach_tail, dist = item
    min_space_needed = 30
    if space >= min_space_needed:
        if can_reach_tail:
            return (0, dist, -space)
        else:
            return (1, dist, -space)
    else:
        if can_reach_tail:
            return (2, -space, dist)
        else:
            # This is the case: space=5 < 30, can_reach_tail=False
            return (3, -space, dist)

print("Rank (8,1):", rank_move(("down", 5, False, 5))) # if dist from (8,1) was 5
print("Rank (9,2):", rank_move(("right", 5, False, 6))) # if dist from (9,2) was 6
