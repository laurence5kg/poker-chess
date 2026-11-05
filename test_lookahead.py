import tournament_engine_core as tec

def minimax_eval(game, p):
    enemy = 'black' if p == 'red' else 'red'
    flag_pos = (0, 0) if enemy == 'red' else (11, 0)
    my_flag = (0, 0) if p == 'red' else (11, 0)

    # Material balance + positional heuristic
    score = 0
    for r in range(12):
        for c in range(5):
            card = game.board[r][c]
            if not card: continue
            val = 0
            if card.is_flag: val = 100000
            elif card.is_bomb: val = 1500
            elif card.is_landmine: val = 800
            elif card.is_sapper or card.is_mochigoma: val = 600
            else: val = 100 + card.rank_val * 50

            # Distance to enemy flag
            if not card.is_immobile:
                d = abs(r - flag_pos[0]) + abs(c - flag_pos[1])
                val += (20 - d) * 15

            if card.player == p: score += val
            else: score -= val

    # Mochigoma in hand
    for c in game.hands[p]['mochigoma']: score += 700
    for c in game.hands[enemy]['mochigoma']: score -= 700
    return score

print("Minimax evaluator written.")
