import run_10_ladder_1000 as r10

v10 = r10.STRAT_REGISTRY['v10']

def m11(game, p):
    acts = game.get_actions(p)
    if not acts: return None
    enemy = 'black' if p == 'red' else 'red'
    flag_pos = (0, 0) if enemy == 'red' else (11, 0)

    # 1. Instant Mate
    for a in acts:
        if a['type'] == 'move' and a['to'] == flag_pos: return a

    # 2. Checkmate Mochigoma Drop
    adj_flag = [(flag_pos[0]+1, flag_pos[1]), (flag_pos[0], flag_pos[1]+1)] if enemy == 'red' else [(flag_pos[0]-1, flag_pos[1]), (flag_pos[0], flag_pos[1]+1)]
    for a in acts:
        if a['type'] == 'drop' and a['to'] in adj_flag and a['hand'] == 'mochigoma':
            tr, tc = a['to']
            if game.board[tr][tc] is None and (tr, tc) not in game.known_mines[p]:
                return a

    # Flank Pincer Priority: High officer actively pushes on Col 4
    for a in acts:
        if a['type'] == 'move':
            fr, fc = a['from']
            tr, tc = a['to']
            c = a['card']
            if fc == 4 and tc == 4 and c.rank_val >= 8:
                if (p == 'red' and tr > fr) or (p == 'black' and tr < fr):
                    a['s'] = 999999
                    return a

    return v10(game, p)

r10.STRAT_REGISTRY['m11'] = m11

w_new = 0
w_old = 0
draws = 0
for g_num in range(10):
    if g_num % 2 == 0:
        w, _ = r10.play_match('m11', 'v10', tier1=1, tier2=1)
        if w == 'red': w_new += 1
        elif w == 'black': w_old += 1
        else: draws += 1
    else:
        w, _ = r10.play_match('v10', 'm11', tier1=1, tier2=1)
        if w == 'black': w_new += 1
        elif w == 'red': w_old += 1
        else: draws += 1

print(f"M11 vs V10: Wins={w_new}, Losses={w_old}, Draws={draws}")
