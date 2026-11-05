import tournament_engine_core as tec
from test_v1_run import v0, v1

def v2(game, p):
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

    # 2. Defend Homeland Corridor: Intercept any intruder on Column 0
    for a in acts:
        if a['type'] == 'move' and a['target'] and a['target'].player == enemy:
            tr, tc = a['to']
            if tc == 0:
                c = a['card']
                k = game.memory[p].get(a['target'].id)
                if c.is_bomb or not k or c.rank_val >= k.get('rank_val', 0):
                    return a

    # 3. Deploy Reserves on Row 4 / Row 7
    for a in acts:
        if a['type'] == 'drop' and a['hand'] == 'starting':
            tr, tc = a['to']
            if (p == 'red' and tr == 4) or (p == 'black' and tr == 7):
                return a

    # 4. Standard Heuristic
    for a in acts:
        s = 20
        if a['type'] == 'move':
            fr, fc = a['from']
            tr, tc = a['to']
            c = a['card']
            tgt = a['target']
            my_r = c.rank_val
            is_sapper = c.is_sapper or c.is_mochigoma

            # SAPPER PRESERVATION: Sapper MUST NOT rush ahead without protection!
            if is_sapper:
                # Keep sapper safe behind front line until enemy pieces in column 0 are cleared
                if (p == 'red' and tr >= 6) or (p == 'black' and tr <= 5):
                    # Check if enemy piece is ahead in column 0
                    ahead = any(game.board[r][0] and game.board[r][0].player == enemy for r in range(12))
                    if ahead:
                        s -= 80000

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
                    if is_sapper: s -= 50000 # Do not blind attack with sapper
                    elif my_r in [2, 3]: s += 2000 # Probe with 2, 3
                    elif my_r >= 8: s += 1000 # Heavy attack
                    else: s += 50

            # Advance along column 0 with heavy officers
            if fc == 0 and tc == 0 and my_r >= 6:
                if (p == 'red' and tr > fr) or (p == 'black' and tr < fr):
                    s += 600

            # Forward movement
            if p == 'red' and tr > fr: s += 35
            if p == 'black' and tr < fr: s += 35

            # If barrier mine is cleared or known, sapper rushes it
            if is_sapper:
                d_bm = abs(tr - barrier_mine[0]) + abs(tc - barrier_mine[1])
                old_d = abs(fr - barrier_mine[0]) + abs(fc - barrier_mine[1])
                if d_bm < old_d: s += 8000
        elif a['type'] == 'drop':
            s += 20
        a['s'] = s
    acts.sort(key=lambda x: x['s'], reverse=True)
    return acts[0]

tec.STRAT_REGISTRY['v2'] = v2

print("Testing V2 vs V1 (100 games)...")
w, l, d, rate, dt = tec.run_tournament_stage('v2', 'v1', 1, 1, 100)
print(f"STAGE 2 (V2 vs V1): W={w}, L={l}, D={d}, Decisive Rate={rate:.1f}% in {dt:.1f}s")
