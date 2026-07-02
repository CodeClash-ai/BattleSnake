"""
Port of "Untimely Neglected Wearable" (version: unwinder) by altersaddle.
Original: https://github.com/altersaddle/untimely-neglected-wearable (snakebrain.py + server.py)

The original already targets the Battlesnake v1 API (bottom-left origin, y-up), so no
coordinate remap is needed. The heuristics below reproduce snakebrain.get_smart_moves /
get_safe_moves faithfully. The only adaptations:
  * The CodeClash v1 state has no "game"/"ruleset" object, so all ruleset-dependent
    branches (wrapped mode, hazardDamagePerTurn) are guarded to tolerate a missing/empty
    ruleset. With no hazards and standard rules this matches the original's behavior.
  * server.py's move() wiring (set_globals -> get_smart_moves -> random.choice) is
    reproduced. Everything is wrapped in try/except that always returns a legal move.
"""

import random

MOVE_LOOKUP = {"left": -1, "right": 1, "up": 1, "down": -1}
_game = None
_board = None


def set_globals(game, board):
    global _game
    global _board
    # Unlike the original (which caches only once via server object reuse), we refresh
    # every turn because each move() call is independent here.
    _game = game
    _board = board


def _ruleset_name():
    if _game and 'ruleset' in _game and _game['ruleset']:
        return _game['ruleset'].get('name')
    return None


def _hazard_damage():
    if (_game and _game.get('ruleset') and _game['ruleset'].get('settings')
            and _game['ruleset']['settings'].get('hazardDamagePerTurn')):
        return _game['ruleset']['settings']['hazardDamagePerTurn']
    return None


def is_wrapped():
    return _ruleset_name() == 'wrapped'


def get_next(current_head, next_move):
    future_head = current_head.copy()

    if next_move in ["left", "right"]:
        future_head["x"] = current_head["x"] + MOVE_LOOKUP[next_move]
    elif next_move in ["up", "down"]:
        future_head["y"] = current_head["y"] + MOVE_LOOKUP[next_move]

    if _game and _board:
        if _ruleset_name() == 'wrapped':
            if future_head["x"] <= -1:
                future_head["x"] = _board["width"] - 1
            if future_head["x"] >= _board["width"]:
                future_head["x"] = 0
            if future_head["y"] <= -1:
                future_head["y"] = _board["height"] - 1
            if future_head["y"] >= _board["height"]:
                future_head["y"] = 0

    return future_head


def get_all_moves(coord):
    return [{'x': coord['x'], 'y': coord['y'] + 1}, {'x': coord['x'], 'y': coord['y'] - 1},
            {'x': coord['x'] + 1, 'y': coord['y']}, {'x': coord['x'] - 1, 'y': coord['y']}]


def get_reverse(move):
    reverse_moves = {"left": "right", "right": "left", "up": "down", "down": "up"}
    return reverse_moves[move]


def get_safe_moves(possible_moves, body, board, squadmates=None, my_snake=None):
    safe_moves = []

    for guess in possible_moves:
        guess_coord = get_next(body[0], guess)
        if avoid_walls(guess_coord, board["width"], board["height"]) and avoid_snakes(guess_coord, board["snakes"]):
            safe_moves.append(guess)
        elif len(body) > 1 and guess_coord == body[-1] and guess_coord not in body[:-1]:
            safe_moves.append(guess)
        if squadmates and my_snake:
            for snake in squadmates:
                if guess_coord in snake["body"][1:] and guess_coord not in my_snake["body"][:-1]:
                    safe_moves.append(guess)
        hazard_damage = _hazard_damage()
        if hazard_damage:
            if guess_coord in board['hazards'] and my_snake and hazard_damage > my_snake['health']:
                while guess in safe_moves:
                    safe_moves.remove(guess)
    return safe_moves


def avoid_walls(future_head, board_width, board_height):
    result = True

    if is_wrapped():
        return True

    x = int(future_head["x"])
    y = int(future_head["y"])

    if x < 0 or y < 0 or x >= board_width or y >= board_height:
        result = False

    return result


def avoid_snakes(future_head, snake_bodies):
    for snake in snake_bodies:
        if future_head in snake["body"][:-1]:
            return False
    return True


def avoid_consumption(future_head, snake_bodies, my_snake):
    if len(snake_bodies) < 2:
        return True

    my_length = my_snake["length"]
    for snake in snake_bodies:
        if snake == my_snake:
            continue
        if future_head in get_all_moves(snake["head"]) and future_head not in snake["body"][1:-1] and my_length <= snake["length"]:
            return False
    return True


def avoid_food(future_head, food):
    return future_head not in food


def avoid_hazards(future_head, hazards):
    return not future_head in hazards


def get_shortest_distance(start_coord, end_coord):
    choices = []
    choices.append(abs(end_coord["x"] - start_coord["x"]) + abs(end_coord["y"] - start_coord["y"]))
    if is_wrapped():
        choices.append(abs(end_coord["x"] + _board["width"] - start_coord["x"]) + abs(end_coord["y"] - start_coord["y"]))
        choices.append(abs(end_coord["x"] - start_coord["x"]) + abs(end_coord["y"] + _board["height"] - start_coord["y"]))
        choices.append(abs(end_coord["x"] + _board["width"] - start_coord["x"]) + abs(end_coord["y"] + _board["height"] - start_coord["y"]))
    return min(choices)


def get_minimum_moves(start_coord, targets):
    steps = []
    for coord in targets:
        steps.append(get_shortest_distance(start_coord, coord))
    return min(steps)


def get_closest_enemy_head_distance(head_coord, other_snakes):
    steps = [100]
    for snake in other_snakes:
        steps.append(get_shortest_distance(head_coord, snake['head']))
    return min(steps)


def get_closest_enemy(head_coord, other_snakes):
    close_snakes = []
    distance = get_closest_enemy_head_distance(head_coord, other_snakes)
    for snake in other_snakes:
        if get_shortest_distance(head_coord, snake['head']) == distance:
            close_snakes.append(snake)
    return close_snakes


def get_body_segment_count(coord, move, snakes):
    retval = 0
    for snake in snakes:
        for segment in snake["body"]:
            if move == 'up' and segment['y'] > coord['y']:
                retval += 1
            elif move == 'down' and segment['y'] < coord['y']:
                retval += 1
            elif move == 'right' and segment['x'] > coord['x']:
                retval += 1
            elif move == 'left' and segment['x'] < coord['x']:
                retval += 1
    return retval


def get_future_head_positions(body, turns, board):
    turn = 0
    explores = {}
    explores[0] = [body[0]]
    while turn < turns:
        turn += 1
        explores[turn] = []
        for test in explores[turn - 1]:
            next_paths = get_safe_moves(["left", "right", "up", "down"], [test], board)
            for path in next_paths:
                explores[turn].append(get_next(test, path))

    return explores[turns]


def get_bypass(origin, target):
    bypass_options = []
    options = get_moves_toward(origin, target)
    x_diff = abs(target['x'] - origin['x'])
    y_diff = abs(target['y'] - origin['y'])
    if x_diff > y_diff:
        bypass_options = ['up', 'down']
    elif x_diff < y_diff:
        bypass_options = ['left', 'right']

    return [move for move in bypass_options if move in options]


def should_choose(moves, squad, snake_count):
    if snake_count <= 1:
        return False
    elif squad or snake_count > 2:
        return len(moves) >= 2
    else:
        return len(moves) == 2


def line_to_safety(direction, start, board):
    retval = 0
    next_coord = get_next(start, direction)
    explored = []
    while next_coord in board["hazards"] and avoid_walls(next_coord, board["width"], board["height"]) and next_coord not in explored:
        next_coord = get_next(next_coord, direction)
        explored.append(next_coord)
        retval += 1
    if not avoid_walls(next_coord, board["width"], board["height"]):
        retval += max([board["width"], board["height"]]) + 1
    return retval


def steps_to_safety(direction, start, board):
    escape_route = [get_next(start, direction)]
    next_coord = escape_route[0]
    extra_cost = 0
    while next_coord in board["hazards"] and avoid_walls(next_coord, board["width"], board["height"]) and extra_cost == 0 and len(escape_route) < 100:
        costs = {}
        for choice in get_safe_moves([move for move in ["up", "down", "left", "right"] if move != get_reverse(direction)], escape_route, board):
            costs[choice] = line_to_safety(choice, get_next(next_coord, choice), board)
        if costs:
            bestway = min(costs.values())
            for choice in costs.keys():
                if costs[choice] == bestway:
                    direction = choice
        next_coord = get_next(next_coord, direction)
        if next_coord in escape_route:
            extra_cost += len(escape_route)
        else:
            escape_route.insert(0, next_coord)
    if not avoid_walls(next_coord, board["width"], board["height"]):
        extra_cost += max([board["width"], board["height"]])
    return len(escape_route) + extra_cost


def at_wall(coord, board):
    if _game and 'ruleset' in _game and _game['ruleset'] and _game['ruleset'] == 'wrapped':
        return False
    return coord["x"] <= 0 or coord["y"] <= 0 or coord["x"] >= board["width"] - 1 or coord["y"] >= board["height"] - 1


def first_three_segments_straight(body):
    return body[0]['x'] == body[2]['x'] or body[0]['y'] == body[2]['y']


def avoid_crowd(moves, enemy_snakes, my_snake):
    crowd_cost = {}

    if 'up' in moves:
        others = [snake for snake in enemy_snakes if snake['head']['y'] > my_snake['head']['y']]
        threats = [snake for snake in others if snake['length'] > my_snake['length'] and get_minimum_moves(my_snake['head'], [snake['head']]) <= 4]
        crowd_cost['up'] = len(others) + (len(threats) * 3)
    if 'down' in moves:
        others = [snake for snake in enemy_snakes if snake['head']['y'] < my_snake['head']['y']]
        threats = [snake for snake in others if snake['length'] > my_snake['length'] and get_minimum_moves(my_snake['head'], [snake['head']]) <= 4]
        crowd_cost['down'] = len(others) + (len(threats) * 3)
    if 'left' in moves:
        others = [snake for snake in enemy_snakes if snake['head']['x'] < my_snake['head']['x']]
        threats = [snake for snake in others if snake['length'] > my_snake['length'] and get_minimum_moves(my_snake['head'], [snake['head']]) <= 4]
        crowd_cost['left'] = len(others) + (len(threats) * 3)
    if 'right' in moves:
        others = [snake for snake in enemy_snakes if snake['head']['x'] > my_snake['head']['x']]
        threats = [snake for snake in others if snake['length'] > my_snake['length'] and get_minimum_moves(my_snake['head'], [snake['head']]) <= 4]
        crowd_cost['right'] = len(others) + (len(threats) * 3)

    return [move for move in moves if crowd_cost[move] == min(crowd_cost.values())]


def is_drafting(my_snake, other_snake):
    neck = my_snake["body"][1]
    if abs(other_snake["head"]["x"] - my_snake["head"]["x"]) > 1:
        return False
    if abs(other_snake["head"]["y"] - my_snake["head"]["y"]) > 1:
        return False
    return other_snake["head"]["x"] == neck["x"] or other_snake["head"]["y"] == neck["y"]


def continue_draft(moves, my_snake, other_snake):
    retval = []
    neck = my_snake["body"][1]
    if other_snake["head"]["x"] < my_snake["head"]["x"] and neck["x"] == other_snake["head"]["x"]:
        retval.append("right")
    if other_snake["head"]["x"] > my_snake["head"]["x"] and neck["x"] == other_snake["head"]["x"]:
        retval.append("left")
    if other_snake["head"]["y"] < my_snake["head"]["y"] and neck["y"] == other_snake["head"]["y"]:
        retval.append("up")
    if other_snake["head"]["y"] > my_snake["head"]["y"] and neck["y"] == other_snake["head"]["y"]:
        retval.append("down")
    return [move for move in moves if move in retval]


def get_excluded_path(path, moves, origin):
    retval = []
    for coord in path:
        if "up" in moves and coord['y'] < origin['y']:
            retval.append(coord)
        if "down" in moves and coord['y'] > origin['y'] and coord not in retval:
            retval.append(coord)
        if "right" in moves and coord['x'] < origin['x'] and coord not in retval:
            retval.append(coord)
        if "left" in moves and coord['x'] > origin['x'] and coord not in retval:
            retval.append(coord)
    return retval


def retrace_path(path, origin, snake_bodies=None):
    retval = []
    next_moves = [move for move in get_all_moves(origin) if move in path]
    slice_counter = -1
    while next_moves:
        step = []
        body_coords = []
        if snake_bodies:
            for snake in snake_bodies:
                body_coords += snake['body'][:slice_counter]
                if len(snake['body']) > abs(slice_counter):
                    path += snake['body'][slice_counter]
        for coord in next_moves:
            retval.append(coord)
            step += [move for move in get_all_moves(coord) if move in path and move not in step and move not in retval and move not in body_coords]
        next_moves = step
        slice_counter -= 1
    return retval


def get_moves_toward(start_coord, end_coord):
    retval = []
    if end_coord['x'] > start_coord['x']:
        retval.append('right')
    if end_coord['x'] < start_coord['x']:
        retval.append('left')
    if end_coord['y'] > start_coord['y']:
        retval.append('up')
    if end_coord['y'] < start_coord['y']:
        retval.append('down')
    return retval


def hash_coord(coord):
    return f"{coord['x']}:{coord['y']}"


def can_squeeze(body, space):
    return body[-1] in space


def get_smart_moves(possible_moves, body, board, my_snake):
    smart_moves = []
    food_avoid = []
    avoid_moves = []
    enemy_snakes = []
    squadmates = []
    all_moves = ["up", "down", "left", "right"]
    other_snakes = [snake for snake in board["snakes"] if snake["id"] != my_snake["id"]]
    if my_snake.get("squad"):
        enemy_snakes = [snake for snake in other_snakes if snake["squad"] != my_snake["squad"]]
        squadmates = [snake for snake in other_snakes if snake["squad"] == my_snake["squad"]]
    else:
        enemy_snakes = other_snakes
    safe_moves = get_safe_moves(possible_moves, body, board, squadmates, my_snake)

    tron_mode = len(board['food']) + sum([snake['length'] for snake in board['snakes']]) >= board['width'] * board['height']
    hazard_cost = 14
    hd = _hazard_damage()
    if hd:
        hazard_cost = hd

    eating_snakes = []
    gutter_snakes = []
    gutter_food = []
    safe_coords = {}
    head_distance = {}
    next_coords = {}
    choke_moves = {}
    squeeze_offset = {}
    collision_threats = []
    collision_targets = {}
    dead_ends = {}
    food_step = {}
    hazard_step = {}
    choke_points = {}

    hunger_threshold = board['width'] + my_snake['length'] / 2
    enemy_offset = {}

    for snake in enemy_snakes:
        if any(eat_coord in get_all_moves(snake['head']) for eat_coord in board['food']):
            enemy_offset[snake['id']] = 1
        else:
            enemy_offset[snake['id']] = 0
        enemy_offset[snake['id']] += len(snake['body']) - len(list(map(dict, frozenset(frozenset(i.items()) for i in snake['body']))))
        if snake['length'] > my_snake['length']:
            enemy_offset[snake['id']] += 2

    for guess in safe_moves:
        safe_coords[guess] = []
        guess_coord = get_next(body[0], guess)
        next_coords[guess] = guess_coord
        explore_edge = [guess_coord]
        all_coords = [guess_coord]
        next_explore = []
        explore_step = 1
        health_cost = 0
        eating_offset = 0
        squeeze_offset[guess] = 0
        food_step[guess] = {}
        choke_points[guess] = {}

        for segments in body[:-1]:
            next_explore.clear()
            explore_step += 1
            if len(explore_edge) == 1 and explore_step > 1:
                squeeze_offset[guess] += 1
            if len(explore_edge) == 0 and guess not in dead_ends:
                dead_ends[guess] = explore_step
            for explore in explore_edge:
                health_cost += 1
                if explore in board['hazards']:
                    health_cost += hazard_cost
                if explore in board['food']:
                    eating_offset += 1
                    food_step[guess][hash_coord(explore)] = explore_step - 1
                    health_cost -= 100
                safe = get_safe_moves(all_moves, [explore], board, squadmates, my_snake)
                for safe_move in safe:
                    guess_coord_next = get_next(explore, safe_move)
                    if guess_coord_next not in all_coords:
                        next_explore.append(guess_coord_next)
                if board['hazards'] and my_snake['head'] in board['hazards'] and explore not in board['hazards'] and guess not in hazard_step.keys() and len(safe) > 2:
                    hazard_step[guess] = explore_step - 1

                if explore_step > 3 and len(explore_edge) == 1:
                    choke_points[guess][explore_step] = explore_edge[0]

                if not tron_mode:
                    snake_collide = [coord for coord in get_all_moves(explore) if not avoid_snakes(coord, enemy_snakes)]
                    if snake_collide:
                        for coord in snake_collide:
                            for snake in enemy_snakes:
                                if coord in snake["body"]:
                                    if snake["body"].index(coord) + explore_step >= len(snake["body"]) + enemy_offset[snake['id']]:
                                        start_segment = snake["body"].index(coord)
                                        if coord not in all_coords:
                                            next_explore.append(coord)
                                    elif coord == snake['head']:
                                        if snake['length'] >= my_snake['length']:
                                            collision_threats.append(snake['id'])
                                        elif snake['id'] not in collision_targets:
                                            collision_targets[snake['id']] = explore_step
                                        elif collision_targets[snake['id']] > explore_step:
                                            collision_targets[snake['id']] = explore_step

                                        unexplored = [coord for coord in explore_edge if coord not in all_coords]
                                        if explore_step > 2 and (len(explore_edge) == 1 or len(next_explore) <= 1) and guess not in choke_moves.keys():
                                            choke_moves[guess] = explore_step
                                    elif at_wall(explore, board) and guess not in choke_moves.keys():
                                        choke_moves[guess] = explore_step

                    self_collide = [coord for coord in get_all_moves(explore) if not avoid_snakes(coord, [my_snake])]
                    if self_collide:
                        for coord in self_collide:
                            if coord in my_snake['body'] and my_snake['body'].index(coord) + explore_step >= len(my_snake['body']) + eating_offset and coord not in all_coords:
                                next_explore.append(coord)
                                if board['hazards'] and my_snake['head'] in board['hazards'] and coord not in board['hazards'] and guess not in hazard_step.keys():
                                    hazard_step[guess] = explore_step - 1
                all_coords += next_explore.copy()
                all_coords.append(explore)
            explore_edge = next_explore.copy()

        safe_coords[guess] += list(map(dict, frozenset(frozenset(i.items()) for i in all_coords)))

    for path in safe_coords.keys():
        guess_coord = get_next(body[0], path)
        if ((len(safe_coords[path]) >= len(body) or
                any(snake["body"][-1] in safe_coords[path] for snake in [snake for snake in board["snakes"] if snake['id'] not in enemy_offset.keys()])) and
                avoid_consumption(guess_coord, board["snakes"], my_snake) and
                avoid_hazards(guess_coord, board["hazards"])
             ):
            smart_moves.append(path)

    for snake in other_snakes:
        enemy_options = get_safe_moves(all_moves, snake['body'], board)
        enemy_all = get_all_moves(snake['head'])
        if len(enemy_options) == 1:
            enemy_must = get_next(snake['body'][0], enemy_options[0])
            if snake['length'] < my_snake['length'] and enemy_must in next_coords.values():
                for move, coord in next_coords.items():
                    if coord == enemy_must:
                        eating_snakes.append(move)
            if at_wall(enemy_must, board) and any(match in enemy_all for match in my_snake['body']):
                gutter_snakes.append(snake)
        elif len(enemy_options) == 2:
            for enemy_move in enemy_options:
                enemy_may = get_next(snake['head'], enemy_move)
                if snake['length'] < my_snake['length'] and enemy_may in next_coords.values():
                    for move, coord in next_coords.items():
                        available_space = retrace_path(get_excluded_path(safe_coords[move], get_moves_toward(my_snake['head'], snake['head']), my_snake['head']), snake['head'], board['snakes'])
                        if move in smart_moves and coord == enemy_may and len(get_safe_moves(all_moves, [coord], board)) > 0 and not at_wall(coord, board) and len(available_space) >= my_snake['length']:
                            eating_snakes.append(move)
        if not eating_snakes and snake['id'] in collision_targets:
            collisions = {}
            min_turns = int(collision_targets[snake['id']] / 2)
            steps_towards_enemy = get_moves_toward(my_snake['head'], snake['head'])
            if min_turns <= 4:
                enemy_possible_positions = get_future_head_positions(snake['body'], min_turns, board)
                for move, coord in next_coords.items():
                    move_targets = get_future_head_positions([coord], min_turns - 1, board)
                    collisions[move] = [coord for coord in move_targets if coord in enemy_possible_positions]
                best_approach = max(collisions, key=lambda x: len(collisions[x]))
                most_hits = max(len(collisions[x]) for x in collisions.keys())
                all_attack_moves = [x for x in collisions.keys() if len(collisions[x]) == most_hits]
                if len(all_attack_moves) > 1:
                    enemy_options = get_safe_moves(all_moves, snake['body'], board)
                    no_pinch = [move for move in all_attack_moves if snake['body'][2] not in get_all_moves(get_next(my_snake['head'], move))]
                    if len(no_pinch) == 1:
                        best_approach = no_pinch[0]
                    else:
                        no_run = [move for move in all_attack_moves if move not in enemy_options]
                        if len(no_run) == 1:
                            best_approach = no_run[0]
                exclusion_origin = snake['head']

                available_space = retrace_path(get_excluded_path(safe_coords[best_approach], steps_towards_enemy, exclusion_origin), get_next(my_snake['head'], best_approach), board['snakes'])

                if best_approach in smart_moves:
                    if len(available_space) < my_snake['length'] and not can_squeeze(my_snake['body'], available_space):
                        choke_moves[best_approach] = min_turns
                    elif min_turns == 1 and (best_approach not in choke_moves.keys() or choke_moves[best_approach] > min_turns + 2):
                        eating_snakes.append(best_approach)

    if gutter_snakes and len(enemy_snakes) == 1:
        gutter_cutoff = [move for move in smart_moves if at_wall(get_next(body[0], move), board)]
        if gutter_cutoff:
            eating_snakes = gutter_cutoff

    if collision_threats:
        danger_snakes = [snake for snake in other_snakes if snake['id'] in collision_threats]
        if len(smart_moves) > 1:
            flee_choice = {}
            for enemy_snake in danger_snakes:
                flee_choices = [move for move in get_moves_toward(enemy_snake['head'], my_snake['head']) if move in safe_coords.keys()]
                if not flee_choices and safe_coords:
                    flee_choices = [move for move in safe_coords.keys() if move not in get_moves_toward(my_snake['head'], enemy_snake['head'])]
                if len(flee_choices) == 1:
                    if len(get_moves_toward(enemy_snake['head'], my_snake['head'])) == 1:
                        flee_choices = [move for move in safe_coords.keys() if move not in get_moves_toward(my_snake['head'], enemy_snake['head'])]
                    else:
                        flee_choices += [move for move in get_bypass(my_snake['head'], enemy_snake['head']) if move in safe_coords.keys()]

                distance = get_minimum_moves(enemy_snake['head'], [my_snake['head']])
                food_min = distance
                escape_space = []

                if distance >= 2:
                    temp_flee_choices = [move for move in flee_choices if not at_wall(get_next(my_snake['head'], move), board)]
                    if temp_flee_choices:
                        flee_choices = temp_flee_choices
                if len(flee_choices) == 1:
                    escape_space = retrace_path(get_excluded_path(safe_coords[flee_choices[0]], flee_choices, my_snake['head']), my_snake['head'])

                if enemy_snake['length'] == my_snake['length'] or len(escape_space) >= my_snake['length']:
                    all_food = [min(array) for array in [x.values() for x in food_step.values() if x.values()]]
                    if all_food:
                        food_min = min(all_food)

                if distance <= 4 and flee_choices and distance <= food_min:
                    for move in flee_choices:
                        exclusion_zone = [exclude for exclude in get_safe_moves(all_moves, my_snake['body'], board) if exclude != get_reverse(move)]
                        available_space = retrace_path(get_excluded_path(safe_coords[move], exclusion_zone, enemy_snake['head']), get_next(my_snake['head'], move))
                        if len(available_space) >= my_snake['length'] or my_snake['body'][-1] in available_space:
                            flee_choice[move] = distance
            if flee_choice:
                smart_moves = [move for move in flee_choice.keys() if flee_choice[move] == min(flee_choice.values())]
        elif len(smart_moves) == 1:
            for enemy_snake in danger_snakes:
                enemy_possible_positions = get_future_head_positions(enemy_snake['body'], 1, board)
                my_possible_positions = get_future_head_positions(my_snake['body'], 1, board)
                my_best = [coord for coord in my_possible_positions if coord not in enemy_possible_positions]
                shared = [coord for coord in my_possible_positions if coord in enemy_possible_positions]
                exclusion_zone = [move for move in get_safe_moves(all_moves, my_snake['body'], board) if move != get_reverse(smart_moves[0])]
                available_space = retrace_path(get_excluded_path(safe_coords[smart_moves[0]], exclusion_zone, enemy_snake['head']), get_next(my_snake['head'], smart_moves[0]))
                if len(shared) > 1 and len(my_best) == 1 and len(available_space) < my_snake['length'] and my_snake['body'][-1] not in available_space and my_best[0] == get_next(my_snake['head'], smart_moves[0]):
                    flee = get_reverse(smart_moves[0])
                    if flee in safe_coords.keys() and (len(safe_coords[flee]) >= my_snake['length'] or any(snake['body'][-1] in safe_coords[flee] for snake in board['snakes'])):
                        smart_moves = [flee]
        else:
            if len(danger_snakes) == 1:
                enemy_snake = danger_snakes[0]
                if at_wall(my_snake['head'], board) and not at_wall(enemy_snake['head'], board) and get_minimum_moves(my_snake['head'], [enemy_snake['head']]) <= 4:
                    smart_moves = [move for move in safe_coords.keys() if at_wall(get_next(my_snake['head'], move), board)]

    if not eating_snakes and (collision_threats or collision_targets) and choke_moves and smart_moves and len(smart_moves) > 1:
        temp_chokes = [move for move in choke_moves.keys() if choke_moves[move] - squeeze_offset[move] < my_snake['length'] / 2 + 1]
        temp_moves = [move for move in smart_moves if move not in temp_chokes]
        if temp_moves:
            smart_moves = temp_moves

    if not smart_moves and my_snake['head'] not in board['hazards']:
        tail_neighbors = []
        tail_safe = get_safe_moves(all_moves, [body[-1]], board)
        for tail_safe_direction in tail_safe:
            tail_neighbors.append(get_next(body[-1], tail_safe_direction))

        for path in safe_coords.keys():
            if any(coord in safe_coords[path] for coord in tail_neighbors) or body[-1] in safe_coords[path]:
                smart_moves.append(path)
        if not smart_moves:
            for move in all_moves:
                test_move = get_next(body[0], move)
                if test_move == body[-1] and test_move not in body[:-1]:
                    smart_moves.append(move)
        if not smart_moves:
            for move in safe_coords.keys():
                test_move = get_next(body[0], move)
                for snake in other_snakes:
                    if test_move == snake["body"][-1] and test_move not in body[:-1] and not any(coord in board["food"] for coord in get_all_moves(snake["body"][0])):
                        smart_moves.append(move)

    if board['food'] and (my_snake["health"] < hunger_threshold or any(snake["length"] + len(board['food']) >= my_snake["length"] for snake in enemy_snakes)):
        gutter_food = [food for food in board['food'] if at_wall(food, board) and get_minimum_moves(my_snake['head'], [food]) < 2]
        if at_wall(my_snake['head'], board):
            gutter_food += [food for food in board['food'] if (food['x'] == my_snake['head']['x'] or food['y'] == my_snake['head']['y']) and get_moves_toward(my_snake['head'], food) and get_moves_toward(my_snake['head'], food)[0] in safe_coords.keys()]

    if smart_moves and not gutter_snakes and not gutter_food and my_snake["length"] >= 4:
        gutter_avoid = [move for move in smart_moves if not at_wall(get_next(body[0], move), board)]
        if gutter_avoid:
            smart_moves = gutter_avoid

    if safe_coords and not smart_moves and my_snake['head'] not in board['hazards']:
        if other_snakes:
            escape_plan = {}
            for snake in other_snakes:
                if abs(my_snake['head']['x'] - snake['head']['x']) <= 2 and abs(my_snake['head']['y'] - snake['head']['y']) <= 2:
                    for move in safe_coords.keys():
                        escape_plan[move] = len(get_safe_moves(all_moves, [get_next(my_snake['head'], move)], board))
            if escape_plan:
                for move in escape_plan.keys():
                    if escape_plan[move] == max(escape_plan.values()) and move not in smart_moves:
                        smart_moves.append(move)
        if not smart_moves:
            max_squeeze = max(map(len, safe_coords.values()))
            squeeze_moves = [move for move in safe_coords.keys() if len(safe_coords[move]) == max_squeeze]
            max_deadend = -1
            if len(squeeze_moves) > 1:
                if dead_ends:
                    max_deadend = max(dead_ends.values())
                    squeeze_moves = [move for move in dead_ends.keys() if dead_ends[move] == max_deadend and move in squeeze_moves]
            for squeeze_move in squeeze_moves:
                if len(safe_coords[squeeze_move]) > 2 and avoid_consumption(get_next(body[0], squeeze_move), board["snakes"], my_snake):
                    smart_moves.append(squeeze_move)

    food_targets = []
    if board['food']:
        food_targets = [food for food in board['food'] if food not in board['hazards']]

    if (len(smart_moves) > 1 or my_snake['head'] in board['hazards']) and board['food'] and not eating_snakes and (my_snake["health"] < hunger_threshold or any(snake["length"] + (len(food_targets) / 2) >= my_snake["length"] for snake in enemy_snakes)):
        food_choices = smart_moves
        food_moves = {}
        closest_food = []
        greed_moves = []
        if not food_targets or my_snake['head'] in board['hazards']:
            food_targets = board["food"]

        if my_snake['health'] < hunger_threshold or my_snake["length"] < board['width']:
            food_choices = safe_coords.keys()

        for path in food_choices:
            if any(food in safe_coords[path] for food in food_targets):
                food_moves[path] = get_minimum_moves(get_next(body[0], path), [food for food in food_targets if food in safe_coords[path]])
                if food_step[path]:
                    target_keys = [hash_coord(food) for food in food_targets if food in safe_coords[path]]
                    target_keys = [key for key in target_keys if key in food_step[path].keys()]
                    target_steps = [food_step[path][key] for key in target_keys]
                    if target_steps:
                        food_moves[path] = min(target_steps)

        if food_moves:
            closest_food_distance = min(food_moves.values())
            food_considerations = other_snakes
            if squadmates and my_snake['name'] == min([snake['name'] for snake in board['snakes'] if snake['squad'] == my_snake['squad']]):
                food_considerations = enemy_snakes
            if my_snake['head'] in board['hazards'] and closest_food_distance > 2:
                food_considerations = []
            for path in food_moves.keys():
                if food_moves[path] <= closest_food_distance:
                    closest_food.append(path)
                    minimum_moves_threshold = 6
                    for food in food_targets:
                        test_coord = get_next(my_snake["head"], path)
                        distance_to_me = get_minimum_moves(food, [test_coord])
                        if food_step[path] and hash_coord(food) in food_step[path].keys():
                            distance_to_me = food_step[path][hash_coord(food)]
                        if distance_to_me == food_moves[path]:
                            for snake in food_considerations:
                                if food in get_all_moves(snake['head']) and distance_to_me > 1 and snake['length'] + 1 >= my_snake['length']:
                                    avoid_moves.append(path)
                                elif get_minimum_moves(food, [snake["head"]]) <= distance_to_me + 1 and get_minimum_moves(snake["head"], [test_coord]) <= minimum_moves_threshold and snake["length"] > my_snake["length"]:
                                    avoid_moves.append(path)
                    if not (path in avoid_moves) and (path in smart_moves):
                        greed_moves.append(path)
        else:
            for path in food_choices:
                food_moves[path] = get_minimum_moves(get_next(body[0], path), food_targets)
            if food_moves:
                closest_food_distance = min(food_moves.values())
                for path in food_moves.keys():
                    if food_moves[path] <= closest_food_distance and food_moves[path] >= my_snake['length'] and not collision_threats:
                        closest_food.append(path)

        if closest_food:
            if my_snake["health"] < hunger_threshold or greed_moves:
                hazard_avoid = [move for move in closest_food if get_next(body[0], move) not in board['hazards']]
                if hazard_avoid:
                    if greed_moves:
                        smart_moves = greed_moves
                    else:
                        smart_moves = hazard_avoid
                else:
                    smart_moves = closest_food
            else:
                food_intersect = [move for move in smart_moves if move in closest_food and move not in avoid_moves]
                if food_intersect:
                    smart_moves = food_intersect
                elif avoid_moves:
                    avoid_test = [move for move in smart_moves if move not in avoid_moves]
                    if avoid_test:
                        smart_moves = avoid_test
                elif min(food_moves.values()) * 16 < my_snake["health"] and collision_threats:
                    hazard_pay = [move for move in closest_food if get_next(body[0], move) in board['hazards']]
                    if hazard_pay:
                        smart_moves = hazard_pay
    else:
        if len(smart_moves) > 1 and board["food"]:
            food_avoid = [move for move in smart_moves if get_next(body[0], move) not in board["food"]]

    if not eating_snakes and should_choose(smart_moves, my_snake.get("squad"), len(board['snakes'])) and my_snake['length'] > 3:
        body_weight = {}
        for move in smart_moves:
            next_coord = get_next(body[0], move)
            head_distance[move] = get_closest_enemy_head_distance(next_coord, [snake for snake in enemy_snakes if snake['length'] >= my_snake['length']])
            body_weight[move] = get_body_segment_count(next_coord, move, board['snakes'])

        if head_distance and min(head_distance.values()) <= 5:
            if at_wall(my_snake["head"], board) and not at_wall(my_snake["body"][1], board):
                if board["hazards"]:
                    hazard_avoid = [move for move in smart_moves if not any(coord in board["hazards"] for coord in safe_coords[move])]
                    if hazard_avoid:
                        smart_moves = hazard_avoid
                if len(smart_moves) > 1:
                    collision_snakes = [snake for snake in enemy_snakes if snake['id'] in collision_threats]
                    test_moves = smart_moves
                    for snake in collision_snakes:
                        test_moves = [move for move in test_moves if move in get_moves_toward(snake['head'], my_snake['head'])]
                    if test_moves:
                        smart_moves = test_moves
                    else:
                        smart_moves = avoid_crowd(smart_moves, enemy_snakes, my_snake)
            else:
                enemy_threats = get_closest_enemy(my_snake["head"], [snake for snake in other_snakes if snake['length'] > my_snake['length']])
                if len(enemy_threats) == 1 and is_drafting(my_snake, enemy_threats[0]):
                    eating_snakes = continue_draft(smart_moves, my_snake, enemy_threats[0])
                elif any(snake['id'] in collision_threats for snake in enemy_threats):
                    if len(smart_moves) > 1:
                        smart_moves = [move for move in smart_moves if head_distance[move] == max(head_distance.values())]
                    if len(smart_moves) > 1 and at_wall(my_snake["head"], board):
                        smart_moves = [move for move in smart_moves if not at_wall(get_next(body[0], move), board)]
                    if len(smart_moves) > 1:
                        escape_plan = {}
                        for move in smart_moves:
                            escape_plan[move] = len(get_safe_moves(all_moves, [get_next(my_snake['head'], move)], board))
                        smart_moves = [move for move in escape_plan.keys() if escape_plan[move] == max(escape_plan.values())]
                    if len(smart_moves) > 1:
                        smart_moves = [move for move in smart_moves if body_weight[move] == min(body_weight.values())]

    if board["hazards"] and my_snake["head"] in board["hazards"]:
        if not smart_moves:
            smart_moves = [move for move in safe_coords.keys() if move not in avoid_moves]
        if smart_moves and len(smart_moves) > 1:
            if hazard_step:
                hazard_escape_path = [move for move in hazard_step.keys() if hazard_step[move] == min(hazard_step.values())]
                hazard_moves = [move for move in smart_moves if move in hazard_escape_path]
                if hazard_moves:
                    smart_moves = hazard_moves
            if len(smart_moves) > 1:
                shortest_path = min([steps_to_safety(move, my_snake["head"], board) for move in smart_moves])
                smart_moves = [move for move in smart_moves if steps_to_safety(move, my_snake["head"], board) == shortest_path]
    elif eating_snakes:
        temp_moves = [move for move in eating_snakes if move in smart_moves]
        if temp_moves:
            smart_moves = eating_snakes
    elif food_avoid:
        smart_moves = food_avoid

    if len(smart_moves) > 1 and choke_moves:
        temp_chokes = [move for move in choke_moves.keys() if choke_moves[move] < my_snake['length'] / 2]
        temp_moves = [move for move in smart_moves if move not in temp_chokes]
        if temp_moves:
            smart_moves = temp_moves

    if len(smart_moves) > 1:
        from_coord = my_snake['head']
        to_coord = my_snake['body'][-1]
        center_coord = {'x': (board['width'] - 1) / 2, 'y': (board['height'] - 1) / 2}

        if tron_mode:
            to_coord = center_coord
        elif len(enemy_snakes) == 1:
            enemy = enemy_snakes[0]
            if len(enemy['body']) > len(my_snake['body']):
                to_coord = center_coord
            else:
                to_coord = enemy['head']
        else:
            from_coord = my_snake['body'][2]

        idle_target = get_moves_toward(from_coord, to_coord)
        test_moves = [move for move in smart_moves if move in idle_target]
        if test_moves:
            smart_moves = test_moves

    return smart_moves


# ---------------------------------------------------------------------------
# CodeClash v1 API glue (reproduces server.py's move() wiring)
# ---------------------------------------------------------------------------

def info():
    return {
        "apiversion": "1",
        "author": "altersaddle",
        "color": "#306448",
        "head": "default",
        "tail": "default",
    }


def start(game_state):
    return None


def end(game_state):
    return None


def _fallback_move(game_state):
    """Guaranteed-legal move: in-bounds and not into any snake body (excluding tails)."""
    try:
        you = game_state["you"]
        board = game_state["board"]
        head = you["body"][0]
        w, h = board["width"], board["height"]
        blocked = set()
        for snake in board["snakes"]:
            b = snake["body"]
            for seg in b[:-1]:
                blocked.add((seg["x"], seg["y"]))
        for move in ("up", "down", "left", "right"):
            nc = get_next(head, move)
            if 0 <= nc["x"] < w and 0 <= nc["y"] < h and (nc["x"], nc["y"]) not in blocked:
                return move
    except Exception:
        pass
    return "up"


def move(game_state):
    try:
        board = game_state["board"]
        you = game_state["you"]
        body = you["body"]

        # CodeClash v1 has no "game"/"ruleset". Provide None so ruleset-dependent
        # branches (wrapped mode, hazard damage) stay inert, matching standard rules.
        game = game_state.get("game")
        set_globals(game, board)

        possible_moves = ["up", "down", "left", "right"]
        safe_moves = get_safe_moves(possible_moves, body, board)
        smart_moves = get_smart_moves(possible_moves, body, board, you)

        chosen = None
        if smart_moves:
            chosen = random.choice(smart_moves)
        elif safe_moves:
            chosen = random.choice(safe_moves)

        # Validate the chosen move is legal; fall back otherwise.
        if chosen in possible_moves:
            nc = get_next(body[0], chosen)
            w, h = board["width"], board["height"]
            in_bounds = is_wrapped() or (0 <= nc["x"] < w and 0 <= nc["y"] < h)
            self_hit = (nc["x"], nc["y"]) in {(s["x"], s["y"]) for s in body[:-1]}
            if in_bounds and not self_hit:
                return {"move": chosen}

        return {"move": _fallback_move(game_state)}
    except Exception:
        return {"move": _fallback_move(game_state)}


if __name__ == "__main__":
    from server import run_server
    run_server({"info": info, "start": start, "move": move, "end": end})
