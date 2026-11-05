import run_grandmaster_tournaments as rgt

def v1_master(game, p):
    acts = game.get_actions(p)
    if not acts: return None
    enemy = 'black' if p == 'red' else 'red'
    flag_pos = (0, 0) if enemy == 'red' else (11, 0)
    my_flag = (0, 0) if p == 'red' else (11, 0)

    # 1. Mate in 1
    for a in acts:
        if a['type'] == 'move' and a['to'] == flag_pos: return a

    # 2. Defend Flag if enemy within distance 3
    for r in range(12):
        for c in range(5):
            ec = game.board[r][c]
            if ec and ec.player == enemy and abs(r - my_flag[0]) + abs(c - my_flag[1]) <= 3:
                for a in acts:
                    if a['type'] == 'move' and a['to'] == (r, c):
                        if a['card'].rank_val > 0 or a['card'].is_bomb:
                            return a

    # 3. Drop reserves immediately to overwhelm enemy
    for a in acts:
        if a['type'] == 'drop':
            tr, tc = a['to']
            if (p == 'red' and tr == 4) or (p == 'black' and tr == 7):
                return a

    for a in acts:
        s = 15
        if a['type'] == 'move':
            fr, fc = a['from']
            tr, tc = a['to']
            c = a['card']
            tgt = a['target']
            is_sapper = c.is_sapper or c.is_mochigoma
            if tgt and tgt.player == enemy:
                cid = id(tgt)
                k = game.memory[p].get(cid)
                if k:
                    if k['is_flag']: return a
                    elif k['is_landmine']: s += (30000 if is_sapper else -500000)
                    elif k['rank_val'] > 0:
                        if c.is_bomb: s += 30000 + k['rank_val'] * 500
                        elif is_sapper: s = -9999999
                        elif c.rank_val > k['rank_val']: s += 20000 + k['rank_val'] * 300
                        elif c.rank_val == k['rank_val']: s += 30
                        else: s = -9999999
                elif (tr, tc) in game.known_mines[p]: s += (30000 if is_sapper else -500000)
                else: s += 80

            old_d = abs(fr - flag_pos[0]) + abs(fc - flag_pos[1])
            new_d = abs(tr - flag_pos[0]) + abs(tc - flag_pos[1])
            if new_d < old_d: s += 60
            if is_sapper and new_d < old_d: s += 4000

            if p == 'red' and tr > fr: s += 40
            if p == 'black' and tr < fr: s += 40
        elif a['type'] == 'drop': s += 20
        a['s'] = s
    acts.sort(key=lambda x: x['s'], reverse=True)
    return acts[0]

rgt.STRAT_REGISTRY['v1_master'] = v1_master

w, l, d, rate, dt = rgt.run_tournament_stage('v1_master', 'm1_v0', 1, 0, 500)
print(f"V1_MASTER vs M1_V0: Win Rate = {rate:.2f}% (W={w}, L={l}, D={d}) in {dt:.1f}s")
