import tournament_engine_core as tec
from test_v1_run import v0, v1
from test_v2_run import v2
from test_v3_evasion import v3_evasion

# Let's test a Depth-1 Tactical Lookahead Engine
def v4_lookahead(game, p):
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

    # 2. Defend Camp against intruders
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

    # 4. Filter out moves where opponent can capture us for free next turn (Depth-1 Lookahead)
    safe_acts = []
    for a in acts:
        if a['type'] == 'move':
            tr, tc = a['to']
            c = a['card']
            my_r = c.rank_val
            # Check adjacent enemy pieces at destination
            hangs = False
            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nr, nc = tr + dr, tc + dc
                if 0 <= nr < 12 and 0 <= nc < 5:
                    adj = game.board[nr][nc]
                    if adj and adj.player == enemy and not adj.is_flag and not adj.is_landmine:
                        k_adj = game.memory[p].get(adj.id)
                        # If Sapper or known lower officer, it hangs!
                        if c.is_sapper or c.is_mochigoma:
                            hangs = True; break
                        elif k_adj and (k_adj.get('is_bomb') or k_adj.get('rank_val', 0) > my_r):
                            hangs = True; break
                        elif not k_adj and nr in my_camp:
                            pass
            if not hangs:
                safe_acts.append(a)
        else:
            safe_acts.append(a)

    eval_pool = safe_acts if safe_acts else acts

    for a in eval_pool:
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
                    elif my_r in [2, 3]: s += 2000
                    elif my_r >= 8: s += 1000
                    else: s += 50

            # Heavy officer escort on Column 0
            if fc == 0 and tc == 0 and my_r >= 6:
                if (p == 'red' and tr > fr) or (p == 'black' and tr < fr):
                    s += 800

            # Forward movement
            if p == 'red' and tr > fr: s += 35
            if p == 'black' and tr < fr: s += 35

            if is_sapper:
                d_bm = abs(tr - barrier_mine[0]) + abs(tc - barrier_mine[1])
                old_d = abs(fr - barrier_mine[0]) + abs(fc - barrier_mine[1])
                if d_bm < old_d: s += 5000
        elif a['type'] == 'drop':
            s += 20
        a['s'] = s
    eval_pool.sort(key=lambda x: x['s'], reverse=True)
    return eval_pool[0]

tec.STRAT_REGISTRY['v4_lookahead'] = v4_lookahead

print("Testing V4_LOOKAHEAD vs V3_EVASION (100 games)...")
w, l, d, rate, dt = tec.run_tournament_stage('v4_lookahead', 'v3_evasion', 1, 1, 100)
print(f"STAGE 4 (V4_LOOKAHEAD vs V3_EVASION): W={w}, L={l}, D={d}, Decisive Rate={rate:.1f}% in {dt:.1f}s")
