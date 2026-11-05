import run_10_ladder_full as rlf

# Let's test a calibrated v2 that includes reserve drops and camp defense
def v2_fixed(game, p):
    acts = game.get_actions(p)
    if not acts: return None
    enemy = 'black' if p == 'red' else 'red'
    flag_pos = (0, 0) if enemy == 'red' else (11, 0)
    my_flag = (0, 0) if p == 'red' else (11, 0)
    my_camp = [0, 1, 2, 3, 4] if p == 'red' else [11, 10, 9, 8, 7]

    # 1. Mate in 1
    for a in acts:
        if a['type'] == 'move' and a['to'] == flag_pos: return a

    # 2. Immediate Starting Reserves Deployment
    for a in acts:
        if a['type'] == 'drop' and a['hand'] == 'starting':
            tr, tc = a['to']
            if (p == 'red' and tr == 4) or (p == 'black' and tr == 7): return a

    # 3. Intercept threats in camp
    for a in acts:
        if a['type'] == 'move' and a['target'] and a['target'].player == enemy:
            tr, tc = a['to']
            c = a['card']
            if tr in my_camp:
                k = game.memory[p].get(a['target'].id)
                if c.is_bomb or not k or c.rank_val >= k.get('rank_val', 0):
                    return a

    # 4. Standard move scoring with strict veto
    for a in acts:
        s = 20
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
                    elif k['is_landmine']: s += (30000 if is_sapper else -500000)
                    elif k['rank_val'] > 0:
                        if c.is_bomb: s += 30000 + k['rank_val'] * 500
                        elif is_sapper: s = -9999999
                        elif my_r > k['rank_val']: s += 20000 + k['rank_val'] * 300
                        else: s = -9999999
                elif (tr, tc) in game.known_mines[p]: s += (30000 if is_sapper else -500000)
                else:
                    if is_sapper: s -= 40000
                    elif my_r in [2, 3]: s += 2000
                    else: s += 60

            if p == 'red' and tr > fr: s += 35
            if p == 'black' and tr < fr: s += 35
            old_d = abs(fr - flag_pos[0]) + abs(fc - flag_pos[1])
            new_d = abs(tr - flag_pos[0]) + abs(tc - flag_pos[1])
            if new_d < old_d: s += 50
            if is_sapper and new_d < old_d: s += 5000
        elif a['type'] == 'drop': s += 20
        a['s'] = s
    acts.sort(key=lambda x: x['s'], reverse=True)
    return acts[0]

rlf.STRAT_REGISTRY['v2_fixed'] = v2_fixed

w, l, d, rate, dt = rlf.run_tournament_stage('v2_fixed', 'v1', 1, 1, 50)
print(f"Stage 2 (V2_FIXED vs V1): W={w}, L={l}, D={d}, Rate={rate:.1f}%")
