# Let's write a replacement for the rank_move function and test it with Turn 138's values:
# Up: (5, 6) -> space = 5, dist = 5
# Down: (5, 4) -> space = 1, dist = 3

my_length = 24
min_space_needed = min(my_length, 15) # 15

# Let's define the new rank_move function:
def rank_move(item):
    d, space, dist = item
    # We want to prioritize moves that have enough space first.
    # If a move has space >= min_space_needed, we group it as "safe".
    # If a move does not have enough space, we group it as "restricted".
    # Within "safe" moves, we want to minimize distance to target.
    # Within "restricted" moves, we want to maximize space!
    
    if space >= min_space_needed:
        # Safe group: 
        # Primary key: 0 (better than restricted)
        # Secondary key: dist (lower is better)
        # Tertiary key: -space (more space as tie-breaker)
        return (0, dist, -space)
    else:
        # Restricted group:
        # Primary key: 1 (worse than safe)
        # Secondary key: -space (maximize space first and foremost!)
        # Tertiary key: dist (lower is better as tie-breaker)
        return (1, -space, dist)

up_item = ("up", 5, 5)
down_item = ("down", 1, 3)

items = [up_item, down_item]
items.sort(key=rank_move)
print("Sorted items:", items)
# This should correctly output "up" first!
