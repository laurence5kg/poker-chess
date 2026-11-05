import tournament_engine_core as tec
from test_v1_run import v0, v1
from test_v2_run import v2

def v3(game, p):
    acts = game.get_actions(p)
    if not acts: return None
    enemy = 'black' if p == 'red' else 'red'
    flag_pos = (0, 0) if enemy == 'red' else (11, 0)
    my_flag = (0, 0) if p == 'red' else (11, 0)
    barrier_mine = (1, 0) if enemy == 'red' else (10, 0)
    my_camp = [0, 1, 2, 3, 4] if p == 'red' else [11, 10, 9, 8, 7]

    # 1. Instant Flag Capture
    for a in acts:
        if a['type'] == 'move' and a['to'] == flag_pos: return a

    # 2. Defend entire Homeland Camp against intruders (Columns 0, 1, 2, 3, 4)
    for a in acts:
        if a['type'] == 'move' and a['target'] and a['target'].player == enemy:
            tr, tc = a['to']
            c = a['card']
            if tr in my_camp:
                k = game.memory[p].get(a['target'].id)
                if c.is_bomb or not k or c.rank_val >= k.get('rank_val', 0):
                    return a

    # 3. Deploy Reserves on Row 4 / Row 7
    for a in acts:
        if a['type'] == 'drop' and a['hand'] == 'starting':
            tr, tc = a['to']
            if (p == 'red' and tr == 4) or (p == 'black' and tr == 7):
                return a

    # 4. Column 0 Bomb Trap: When enemy pushes col 0, meet it with Bomb!
    for a in acts:
        if a['type'] == 'move' and a['card'].is_bomb:
            tr, tc = a['to']
            if tc == 0 and a['target'] and a['target'].player == enemy:
                return a

    # 5. Advanced Evaluation
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
                    elif k['is_landmine']: s += (100000 if is_sapper else -500000)
                    elif k['rank_val'] > 0:
                        if c.is_bomb: s += 80000 + k['rank_val'] * 1000
                        elif is_sapper: s = -9999999
                        elif my_r > k['rank_val']: s += 40000 + k['rank_val'] * 500
                        else: s = -9999999
                elif (tr, tc) in game.known_mines[p]: s += (100000 if is_sapper else -500000)
                else:
                    if is_sapper: s -= 50000
                    elif c.is_bomb:
                        if tc == 0: s += 60000 # Ambush rushing piece on col 0!
                        else: s += 50
                    elif my_r in [2, 3]: s += 2000
                    elif my_r >= 8: s += 1000
                    else: s += 50

            # Advance along Column 0
            if fc == 0 and tc == 0:
                if my_r >= 6 or c.is_bomb:
                    if (p == 'red' and tr > fr) or (p == 'black' and tr < fr):
                        s += 800

            # Forward movement
            if p == 'red' and tr > fr: s += 40
            if p == 'black' and tr < fr: s += 40

            if is_sapper:
                d_bm = abs(tr - barrier_mine[0]) + abs(tc - barrier_mine[1])
                old_d = abs(fr - barrier_mine[0]) + abs(fc - barrier_mine[1])
                if d_bm < old_d: s += 9000
        elif a['type'] == 'drop':
            s += 20
        a['s'] = s
    acts.sort(key=lambda x: x['s'], reverse=True)
    return acts[0]

tec.STRAT_REGISTRY['v3'] = v3

print("Testing V3 vs V2 (100 games)...")
w, l, d, rate, dt = tec.run_tournament_stage('v3', 'v2', 1, 1, 100)
print(f"STAGE 3 (V3 vs V2): W={w}, L={l}, D={d}, Decisive Rate={rate:.1f}% in {dt:.1f}s")
