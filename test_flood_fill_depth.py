import json

def flood_fill_depth_limited(start, occupied, width, height, max_depth=15):
    if start in occupied:
        return 0
    visited = {start}
    queue = [(start, 0)]
    count = 0
    while queue:
        curr, depth = queue.pop(0)
        count += 1
        if depth >= max_depth:
            continue
        cx, cy = curr
        for nx, ny in [(cx+1, cy), (cx-1, cy), (cx, cy+1), (cx, cy-1)]:
            if 0 <= nx < width and 0 <= ny < height:
                if (nx, ny) not in occupied and (nx, ny) not in visited:
                    visited.add((nx, ny))
                    queue.append(((nx, ny), depth + 1))
    return count

print("Test complete.")
