import re

with open('main.py', 'r') as f:
    content = f.read()

new_logic = r'''
    # Aggressive mode: try to cut off smaller snakes
    my_len = len(game_state["you"]["body"])
    attack_move = None
    
    potential_cutoff_moves = {} # move -> list of snakes it cuts off

    # Find all possible cut-off moves
    for move_option, area in safe_moves_with_area:
        next_coord = get_next_move_coord(my_head, move_option)
        for snake in game_state["board"]["snakes"]:
            if snake["id"] != game_state["you"]["id"] and my_len > len(snake["body"]):
                opp_head = snake["body"][0]
                
                # Predict opponent's possible moves
                opp_possible_moves = ["up", "down", "left", "right"]
                if len(snake["body"]) > 1:
                    opp_neck = snake["body"][1]
                    if opp_neck["x"] < opp_head["x"]: opp_possible_moves.remove("left")
                    elif opp_neck["x"] > opp_head["x"]: opp_possible_moves.remove("right")
                    elif opp_neck["y"] < opp_head["y"]: opp_possible_moves.remove("down")
                    elif opp_neck["y"] > opp_head["y"]: opp_possible_moves.remove("up")

                for opp_move in opp_possible_moves:
                    opp_next_coord = get_next_move_coord(opp_head, opp_move)
                    # Check if our move intercepts one of their potential moves
                    if next_coord['x'] == opp_next_coord['x'] and next_coord['y'] == opp_next_coord['y']:
                         # Make sure the opponent's move would be "safe" for them, otherwise it's not a real path
                        if is_coord_safe(opp_next_coord, board_width, board_height, obstacles):
                            if move_option not in potential_cutoff_moves:
                                potential_cutoff_moves[move_option] = []
                            potential_cutoff_moves[move_option].append(snake['id'])

    # Choose the best cut-off move. The one that cuts off the most snakes,
    # and as a tie-breaker, the one that gives us more space.
    # `safe_moves_with_area` is already sorted by area.
    if potential_cutoff_moves:
        best_cutoff_move = None
        max_cutoff_count = 0
        for move_option, area in safe_moves_with_area:
            if move_option in potential_cutoff_moves:
                cutoff_count = len(potential_cutoff_moves[move_option])
                if cutoff_count > max_cutoff_count:
                    max_cutoff_count = cutoff_count
                    best_cutoff_move = move_option
        if best_cutoff_move:
            attack_move = best_cutoff_move
            print(f"Found cut-off move {attack_move}, cutting off {max_cutoff_count} snake(s)")


    if attack_move:
        next_move = attack_move
    else:
        # Fallback to original adjacent-based aggressive mode
        for move_option, area in safe_moves_with_area:
            next_coord = get_next_move_coord(my_head, move_option)
            for snake in game_state["board"]["snakes"]:
                if snake["id"] != game_state["you"]["id"] and my_len > len(snake["body"]):
                    opp_head = snake["body"][0]
                    if abs(next_coord['x'] - opp_head['x']) + abs(next_coord['y'] - opp_head['y']) == 1:
                        print(f"Found adjacent attack move {move_option} towards snake {snake['id']}")
                        attack_move = move_option
                        break 
            if attack_move:
                break
        
        if attack_move:
            next_move = attack_move
        else:
            # Food-seeking logic, only if not attacking
'''

# The regex needs to be careful with indentation
pattern = re.compile(r"(\s+# Aggressive mode:.*?)(^\s+# Food-seeking logic, only if not attacking)", re.DOTALL | re.MULTILINE)
new_content = pattern.sub(r"\1" + new_logic, content, count=1)

# A bit of a hacky way to fix indentation
# Remove the leading spaces from the replacement block and add the correct indentation from the matched group
leading_spaces = re.search(r'^(\s+)', content.splitlines()[145-1]).group(1)
new_logic_indented = "\n".join([leading_spaces + line for line in new_logic.strip().splitlines()])
# The first line of the new logic is already indented by the replacement
new_content = pattern.sub(leading_spaces.strip() + new_logic_indented, content, count=1)


# Let's try a simpler replacement.
start_line = 145 - 1
end_line = 165 -1
lines = content.splitlines()

# The indentation of the block
indent = ' ' * 4
new_logic_lines = new_logic.strip().splitlines()
indented_new_logic = [indent + line for line in new_logic_lines]

new_lines = lines[:start_line] + indented_new_logic + lines[end_line:]
new_content = "\n".join(new_lines)


with open('main.py', 'w') as f:
    f.write(new_content)

print("Replacement complete.")
