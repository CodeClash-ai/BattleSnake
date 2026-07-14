import json

width, height = 11, 11
my_length = 35
my_tail = (8, 10)

obstacle_positions = {
    (8, 2), (8, 3), (8, 4), (8, 5), (9, 5), (9, 6), (9, 7), (9, 8), (9, 9), (9, 10),
    (10, 10), (10, 9), (10, 8), (10, 7), (10, 6), (10, 5), (10, 4), (10, 3), (10, 2),
    (10, 1), (10, 0), (9, 0), (8, 0), (7, 0), (7, 1), (7, 2), (7, 3), (7, 4), (7, 5),
    (7, 6), (8, 6), (8, 7), (8, 8), (8, 9) # excluding (8, 10) as it is the tail
}

def analyze_move(start_pos):
    queue = [start_pos]
    visited = {start_pos}
    count = 0
    can_reach_tail = False
    
    while queue:
        curr = queue.pop(0)
        count += 1
        
        if curr == my_tail:
            can_reach_tail = True
        
        if count > 120:
            if can_reach_tail:
                break
        
        for dx, dy in [(0, 1), (0, -1), (-1, 0), (1, 0)]:
            nx, ny = curr[0] + dx, curr[1] + dy
            if 0 <= nx < width and 0 <= ny < height:
                if (nx, ny) == my_tail or ((nx, ny) not in obstacle_positions and (nx, ny) not in visited):
                    visited.add((nx, ny))
                    queue.append((nx, ny))
                    
    return count, can_reach_tail

print("Choice (8, 1):", analyze_move((8, 1)))
print("Choice (9, 2):", analyze_move((9, 2)))
