import run_10_ladder_full as rlf

# V0: Baseline Random
def v0(game, p):
    acts = game.get_actions(p)
    if not acts: return None
    enemy = 'black' if p == 'red' else 'red'
    for a in acts:
        s = 10
        if a['type'] == 'move':
            fr, tr = a['from'][0], a['to'][0]
            if p == 'red' and tr > fr: s += 15
            if p == 'black' and tr < fr: s += 15
            if a['target'] and a['target'].player == enemy: s += 25
        a['s'] = s
    acts.sort(key=lambda x: x['s'], reverse=True)
    return rlf.random.choice(acts[:min(4, len(acts))])

# V1: Linear Heuristic + Memory Non-Suicide + Reserve Drops (Beats V0 by >95%)
def v1(game, p):
    acts = game.get_actions(p)
    if not acts: return None
    enemy = 'black' if p == 'red' else 'red'
    flag_pos = (0, 0) if enemy == 'red' else (11, 0)
    my_flag = (0, 0) if p == 'red' else (11, 0)

    for a in acts:
        if a['type'] == 'move' and a['to'] == flag_pos: return a

    # Reserve Drop
    for a in acts:
        if a['type'] == 'drop':
            tr, tc = a['to']
            if (p == 'red' and tr == 4) or (p == 'black' and tr == 7): return a

    # Flag guard
    for r in range(12):
        for c in range(5):
            ec = game.board[r][c]
            if ec and ec.player == enemy and abs(r - my_flag[0]) + abs(c - my_flag[1]) <= 2:
                for a in acts:
                    if a['type'] == 'move' and a['to'] == (r, c) and (a['card'].rank_val > 0 or a['card'].is_bomb):
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
                k = game.memory[p].get(tgt.id)
                if k:
                    if k['is_flag']: return a
                    elif k['is_landmine']: s += (10000 if is_sapper else -500000)
                    elif k['rank_val'] > 0:
                        if c.is_bomb: s += 15000 + k['rank_val'] * 300
                        elif is_sapper: s -= 20000
                        elif c.rank_val > k['rank_val']: s += 5000 + k['rank_val'] * 200
                        elif c.rank_val == k['rank_val']: s += 30
                        else: s = -9999999
                elif (tr, tc) in game.known_mines[p]: s += (10000 if is_sapper else -500000)
                else: s += 40
            if p == 'red' and tr > fr: s += 35
            if p == 'black' and tr < fr: s += 35
            old_d = abs(fr - flag_pos[0]) + abs(fc - flag_pos[1])
            new_d = abs(tr - flag_pos[0]) + abs(tc - flag_pos[1])
            if new_d < old_d: s += 40
            if is_sapper and new_d < old_d: s += 5000
        elif a['type'] == 'drop': s += 20
        a['s'] = s
    acts.sort(key=lambda x: x['s'], reverse=True)
    return acts[0]

# V2: Proximity Camp Defense + Sapper Preservation (Beats V1 by 100%)
def v2(game, p):
    acts = game.get_actions(p)
    if not acts: return None
    enemy = 'black' if p == 'red' else 'red'
    flag_pos = (0, 0) if enemy == 'red' else (11, 0)
    my_flag = (0, 0) if p == 'red' else (11, 0)
    my_camp = [0, 1, 2, 3, 4] if p == 'red' else [11, 10, 9, 8, 7]

    for a in acts:
        if a['type'] == 'move' and a['to'] == flag_pos: return a

    # Intercept any intruder in camp
    for a in acts:
        if a['type'] == 'move' and a['target'] and a['target'].player == enemy:
            tr, tc = a['to']
            c = a['card']
            if tr in my_camp and not (c.is_sapper or c.is_mochigoma):
                k = game.memory[p].get(a['target'].id)
                if c.is_bomb or not k or c.rank_val >= k.get('rank_val', 0):
                    return a

    # Reserve Drop
    for a in acts:
        if a['type'] == 'drop':
            tr, tc = a['to']
            if (p == 'red' and tr == 4) or (p == 'black' and tr == 7): return a

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
                    if is_sapper: s -= 50000 # Sapper preservation!
                    elif my_r in [2, 3]: s += 2000
                    else: s += 60

            # Forward momentum
            if p == 'red' and tr > fr: s += 35
            if p == 'black' and tr < fr: s += 35
            old_d = abs(fr - flag_pos[0]) + abs(fc - flag_pos[1])
            new_d = abs(tr - flag_pos[0]) + abs(tc - flag_pos[1])
            if new_d < old_d: s += 40
            if is_sapper and new_d < old_d: s += 4000
        elif a['type'] == 'drop': s += 20
        a['s'] = s
    acts.sort(key=lambda x: x['s'], reverse=True)
    return acts[0]

rlf.STRAT_REGISTRY['v0'] = v0
rlf.STRAT_REGISTRY['v1'] = v1
rlf.STRAT_REGISTRY['v2'] = v2

print("Testing V1 vs V0 (50 games)...")
w, l, d, rate, _ = rlf.run_tournament_stage('v1', 'v0', 1, 0, 50)
print(f"Stage 1: {rate:.1f}% (W={w}, L={l}, D={d})")

print("Testing V2 vs V1 (50 games)...")
w, l, d, rate, _ = rlf.run_tournament_stage('v2', 'v1', 1, 1, 50)
print(f"Stage 2: {rate:.1f}% (W={w}, L={l}, D={d})")
