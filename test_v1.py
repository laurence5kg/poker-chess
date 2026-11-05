import run_10_models_tournament as r10

def v1_calibrated_defense(game, p):
    acts = game.get_actions(p)
    if not acts: return None
    enemy = 'black' if p == 'red' else 'red'
    flag_pos = (0, 0) if enemy == 'red' else (11, 0)
    my_flag = (0, 0) if p == 'red' else (11, 0)

    # 1. Instant Win
    for a in acts:
        if a['type'] == 'move' and a['to'] == flag_pos: return a

    # 2. Defend Flag if intruder is within 2 steps
    for r in range(12):
        for c in range(5):
            ec = game.board[r][c]
            if ec and ec.player == enemy and abs(r - my_flag[0]) + abs(c - my_flag[1]) <= 2:
                for a in acts:
                    if a['type'] == 'move' and a['to'] == (r, c):
                        if a['card'].rank_val > 0 or a['card'].is_bomb:
                            return a

    for a in acts:
        s = 15
        if a['type'] == 'move':
            fr, fc = a['from']
            tr, tc = a['to']
            c = a['card']
            tgt = a['target']
            my_r = c.rank_val
            is_sapper = c.is_sapper or c.is_mochigoma

            if tgt and tgt.player == enemy:
                k = game.memory[p].get(tgt.id)
                if k:
                    if k['is_flag']: return a
                    elif k['is_landmine']:
                        if is_sapper: s += 60000
                        else: s = -9999999
                    elif k['rank_val'] > 0:
                        if c.is_bomb: s += 70000 + k['rank_val'] * 1000
                        elif is_sapper: s = -9999999
                        elif my_r > k['rank_val']: s += 50000 + k['rank_val'] * 500
                        elif my_r == k['rank_val']: s += 50
                        else: s = -9999999 # Strict Veto
                elif (tr, tc) in game.known_mines[p]:
                    if is_sapper: s += 60000
                    else: s = -9999999
                else:
                    if my_r in [2, 3]: s += 1500
                    elif my_r >= 8: s += 200
                    else: s += 100

            old_d = abs(fr - flag_pos[0]) + abs(fc - flag_pos[1])
            new_d = abs(tr - flag_pos[0]) + abs(tc - flag_pos[1])
            if new_d < old_d: s += 35

            if is_sapper:
                if new_d < old_d: s += 4000

            if p == 'red' and tr > fr: s += 35
            if p == 'black' and tr < fr: s += 35
        elif a['type'] == 'drop':
            s += 25
        a['s'] = s

    acts.sort(key=lambda x: x['s'], reverse=True)
    return acts[0]

r10.STRAT_REGISTRY['v1_calibrated_defense'] = v1_calibrated_defense

w1, w0, d, rate, dt = r10.run_tournament_stage('v1_calibrated_defense', 'v0_baseline', 1, 0, games=200)
print(f"V1 with Defense vs V0: Rate={rate:.2f}%, W1={w1}, W0={w0}, D={d} in {dt:.1f}s")
