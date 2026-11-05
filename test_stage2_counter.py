import run_10_models_tournament as r10
from calibrate_10_ladder import v0, v1

# Let's design V2 to strictly dominate V1
def v2_counter(game, p):
    acts = game.get_actions(p)
    if not acts: return None
    enemy = 'black' if p == 'red' else 'red'
    flag_pos = (0, 0) if enemy == 'red' else (11, 0)
    my_flag = (0, 0) if p == 'red' else (11, 0)
    my_camp = [0, 1, 2, 3, 4] if p == 'red' else [11, 10, 9, 8, 7]
    barrier_mine = (1, 0) if enemy == 'red' else (10, 0)

    # 1. Mate in 1: Flag capture
    for a in acts:
        if a['type'] == 'move' and a['to'] == flag_pos: return a

    # 2. Defend flag if threatened
    for a in acts:
        if a['type'] == 'move' and a['target'] and a['target'].player == enemy:
            tr, tc = a['to']
            if abs(tr - my_flag[0]) + abs(tc - my_flag[1]) <= 2:
                if a['card'].rank_val >= 2 or a['card'].is_bomb:
                    return a

    # 3. Intercept enemy sappers or intruders entering my camp
    for a in acts:
        if a['type'] == 'move' and a['target'] and a['target'].player == enemy:
            tr, tc = a['to']
            tgt = a['target']
            c = a['card']
            # If enemy piece is in our camp or near midline (rows 4, 5, 6, 7)
            if (p == 'black' and tr >= 6) or (p == 'red' and tr <= 5):
                # Ambush with officer >= 5 or bomb
                if c.rank_val >= 5 or c.is_bomb:
                    k = game.memory[p].get(tgt.id)
                    if not k or c.rank_val > k.get('rank_val', 0) or c.is_bomb:
                        return a

    # 4. Standard move evaluation
    for a in acts:
        s = 20
        if a['type'] == 'move':
            fr, fc = a['from']
            tr, tc = a['to']
            c = a['card']
            tgt = a['target']
            my_r = c.rank_val
            is_sapper = c.is_sapper or c.is_mochigoma

            # Never expose sapper prematurely
            if is_sapper and not tgt:
                # Keep sapper safe behind lines until enemy lines are softened
                if (p == 'red' and tr >= 6) or (p == 'black' and tr <= 5):
                    s -= 20000

            if tgt and tgt.player == enemy:
                k = game.memory[p].get(tgt.id)
                if k:
                    if k['is_flag']: return a
                    elif k['is_landmine']: s += (100000 if is_sapper else -500000)
                    elif k['rank_val'] > 0:
                        if c.is_bomb: s += 80000 + k['rank_val'] * 1000
                        elif is_sapper: s = -9999999
                        elif my_r > k['rank_val']: s += 40000 + k['rank_val'] * 500
                        else: s = -9999999
                elif (tr, tc) in game.known_mines[p]: s += (100000 if is_sapper else -500000)
                else:
                    if is_sapper: s -= 40000 # Don't blind suicide sapper
                    elif my_r in [2, 3]: s += 1500 # Probe with 2, 3
                    elif my_r >= 8: s += 500 # Heavy attack
                    else: s += 50

            # Advance officers forward
            if p == 'red' and tr > fr and my_r >= 4: s += 50
            if p == 'black' and tr < fr and my_r >= 4: s += 50

            # When landmine is cleared or known, sapper rushes flag
            if is_sapper and (barrier_mine in game.known_mines[p] or game.board[barrier_mine[0]][barrier_mine[1]] is None):
                d_flag = abs(tr - flag_pos[0]) + abs(tc - flag_pos[1])
                old_d = abs(fr - flag_pos[0]) + abs(fc - flag_pos[1])
                if d_flag < old_d: s += 80000
        elif a['type'] == 'drop':
            # Drop Mochigoma sapper to dismantle mine
            if a['card'].is_sapper or a['card'].is_mochigoma:
                d_bm = abs(a['to'][0] - barrier_mine[0]) + abs(a['to'][1] - barrier_mine[1])
                s += (20 - d_bm) * 500
            else:
                s += 20
        a['s'] = s
    acts.sort(key=lambda x: x['s'], reverse=True)
    return acts[0]

r10.STRAT_REGISTRY['v1'] = v1
r10.STRAT_REGISTRY['v2_counter'] = v2_counter

print("Testing V2_COUNTER vs V1 (50 games)...")
w, l, d, rate, dt = r10.run_tournament_stage('v2_counter', 'v1', 1, 1, 50)
print(f"Result: W={w}, L={l}, D={d}, Rate={rate:.1f}% in {dt:.1f}s")
