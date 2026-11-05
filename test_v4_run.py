import tournament_engine_core as tec
from test_v1_run import v0, v1
from test_v2_run import v2
from test_v3_evasion import v3_evasion

def v4(game, p):
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

    # 2. General Threat Evacuation (for Sapper AND high officers facing higher enemy/bomb)
    for a in acts:
        if a['type'] == 'move':
            c = a['card']
            my_r = c.rank_val
            fr = a['from']
            threatened = False
            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nr, nc = fr[0] + dr, fr[1] + dc
                if 0 <= nr < 12 and 0 <= nc < 5:
                    adj = game.board[nr][nc]
                    if adj and adj.player == enemy:
                        k_adj = game.memory[p].get(adj.id)
                        if c.is_sapper or c.is_mochigoma:
                            if not adj.is_flag and not adj.is_landmine: threatened = True; break
                        elif k_adj:
                            if k_adj.get('is_bomb') or k_adj.get('rank_val', 0) > my_r:
                                threatened = True; break
            if threatened:
                tr, tc = a['to']
                safe = True
                for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    nr, nc = tr + dr, tc + dc
                    if 0 <= nr < 12 and 0 <= nc < 5:
                        adj = game.board[nr][nc]
                        if adj and adj.player == enemy:
                            k_adj = game.memory[p].get(adj.id)
                            if c.is_sapper or c.is_mochigoma:
                                if not adj.is_flag and not adj.is_landmine: safe = False; break
                            elif k_adj:
                                if k_adj.get('is_bomb') or k_adj.get('rank_val', 0) > my_r:
                                    safe = False; break
                if safe:
                    return a

    # 3. Intercept threats in camp or column 0
    for a in acts:
        if a['type'] == 'move' and a['target'] and a['target'].player == enemy:
            tr, tc = a['to']
            c = a['card']
            if tr in my_camp or tc == 0:
                k = game.memory[p].get(a['target'].id)
                if c.is_bomb or not k or c.rank_val >= k.get('rank_val', 0):
                    return a

    # 4. Deploy Reserves on Row 4 / Row 7
    for a in acts:
        if a['type'] == 'drop' and a['hand'] == 'starting':
            tr, tc = a['to']
            if (p == 'red' and tr == 4) or (p == 'black' and tr == 7):
                return a

    # 5. Move Scoring + Guided Bomb Ambush
    for a in acts:
        s = 25
        if a['type'] == 'move':
            fr, fc = a['from']
            tr, tc = a['to']
            c = a['card']
            tgt = a['target']
            my_r = c.rank_val
            is_sapper = c.is_sapper or c.is_mochigoma

            # Threat Zone Avoidance
            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nr, nc = tr + dr, tc + dc
                if 0 <= nr < 12 and 0 <= nc < 5:
                    adj = game.board[nr][nc]
                    if adj and adj.player == enemy:
                        k_adj = game.memory[p].get(adj.id)
                        if is_sapper and not adj.is_flag and not adj.is_landmine:
                            s -= 250000
                        elif k_adj and (k_adj.get('is_bomb') or k_adj.get('rank_val', 0) > my_r):
                            s -= 150000

            if tgt and tgt.player == enemy:
                k = game.memory[p].get(tgt.id)
                if k:
                    if k['is_flag']: return a
                    elif k['is_landmine']: s += (100000 if is_sapper else -500000)
                    elif k['rank_val'] > 0:
                        if c.is_bomb: s += 90000 + k['rank_val'] * 1500
                        elif is_sapper: s = -9999999
                        elif my_r > k['rank_val']: s += 45000 + k['rank_val'] * 500
                        else: s = -9999999
                elif (tr, tc) in game.known_mines[p]: s += (100000 if is_sapper else -500000)
                else:
                    if is_sapper: s -= 50000
                    elif c.is_bomb and tc == 0: s += 70000 # Guided Bomb ambush on Col 0!
                    elif my_r in [2, 3]: s += 2000
                    elif my_r >= 8: s += 1200
                    else: s += 50

            # Heavy officer escort on Column 0
            if fc == 0 and tc == 0 and my_r >= 6:
                if (p == 'red' and tr > fr) or (p == 'black' and tr < fr):
                    s += 850

            # Forward movement
            if p == 'red' and tr > fr: s += 40
            if p == 'black' and tr < fr: s += 40

            if is_sapper:
                d_bm = abs(tr - barrier_mine[0]) + abs(tc - barrier_mine[1])
                old_d = abs(fr - barrier_mine[0]) + abs(fc - barrier_mine[1])
                if d_bm < old_d: s += 6000
        elif a['type'] == 'drop':
            s += 25
        a['s'] = s
    acts.sort(key=lambda x: x['s'], reverse=True)
    return acts[0]

tec.STRAT_REGISTRY['v4'] = v4

print("Testing V4 vs V3_EVASION (100 games)...")
w, l, d, rate, dt = tec.run_tournament_stage('v4', 'v3_evasion', 1, 1, 100)
print(f"STAGE 4 (V4 vs V3_EVASION): W={w}, L={l}, D={d}, Decisive Rate={rate:.1f}% in {dt:.1f}s")
