import run_grandmaster_tournaments as rgt

def m1_v1_probe(game, p):
    acts = game.get_actions(p)
    if not acts: return None
    enemy = 'black' if p == 'red' else 'red'
    flag_pos = (0, 0) if enemy == 'red' else (11, 0)
    my_flag = (0, 0) if p == 'red' else (11, 0)
    my_camp = [0, 1, 2, 3, 4] if p == 'red' else [11, 10, 9, 8, 7]

    for a in acts:
        if a['type'] == 'move' and a['to'] == flag_pos: return a

    for a in acts:
        s = 15
        if a['type'] == 'move':
            fr, fc = a['from']
            tr, tc = a['to']
            c = a['card']
            tgt = a['target']
            my_r = c.rank_val
            is_sapper = c.is_sapper or c.is_mochigoma

            # Defend camp
            if tgt and tgt.player == enemy and tr in my_camp:
                if my_r > 0 or c.is_bomb:
                    s += 120000

            if tgt and tgt.player == enemy:
                cid = id(tgt)
                k = game.memory[p].get(cid)
                if k:
                    if k['is_flag']: return a
                    elif k['is_landmine']: s += (20000 if is_sapper else -500000)
                    elif k['rank_val'] > 0:
                        if c.is_bomb: s += 20000 + k['rank_val'] * 500
                        elif is_sapper: s = -9999999
                        elif my_r > k['rank_val']: s += 10000 + k['rank_val'] * 300
                        elif my_r == k['rank_val']: s += 30
                        else: s = -9999999
                elif (tr, tc) in game.known_mines[p]: s += (20000 if is_sapper else -500000)
                else:
                    # Unrevealed: probe with 2 and 3, NEVER attack with sapper!
                    if is_sapper: s -= 50000
                    elif my_r in [2, 3]: s += 2500
                    elif my_r >= 8: s += 50
                    else: s += 20

            if p == 'red' and tr > fr: s += 30
            if p == 'black' and tr < fr: s += 30
            old_d = abs(fr - flag_pos[0]) + abs(fc - flag_pos[1])
            new_d = abs(tr - flag_pos[0]) + abs(tc - flag_pos[1])
            if new_d < old_d: s += 40
            if is_sapper and new_d < old_d: s += 1000
        elif a['type'] == 'drop': s += 20
        a['s'] = s
    acts.sort(key=lambda x: x['s'], reverse=True)
    return acts[0]

rgt.STRAT_REGISTRY['m1_v1_probe'] = m1_v1_probe

w, l, d, rate, dt = rgt.run_tournament_stage('m1_v1_probe', 'm1_v0', 1, 0, 500)
print(f"M1_V1_PROBE vs M1_V0: Win Rate = {rate:.2f}% (W={w}, L={l}, D={d}) in {dt:.1f}s")
