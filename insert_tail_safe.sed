    # Tail safety check to prevent self-trapping
    tail_safe_moves = []
    for move, area in safe_moves_with_area:
        next_coord = get_next_move_coord(my_head, move)

        # Create a hypothetical next game state
        hypothetical_body = [next_coord] + game_state['you']['body'][:-1]
        hypothetical_game_state = game_state.copy()
        hypothetical_game_state['you'] = game_state['you'].copy()
        hypothetical_game_state['you']['body'] = hypothetical_body
        hypothetical_game_state['you']['head'] = next_coord

        # Check if the tail can still reach the new head
        if is_tail_safe(hypothetical_body[-1], hypothetical_game_state):
            tail_safe_moves.append((move, area))

    if tail_safe_moves:
        print(f"Found {len(tail_safe_moves)} tail-safe moves.")
        safe_moves_with_area = tail_safe_moves
    else:
        print("No tail-safe moves found, falling back to all safe moves.")
