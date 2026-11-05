import tournament_engine_core as tec
from test_v1_run import v0, v1
from test_v2_run import v2
from test_v3_evasion import v3_evasion
from test_v4_convert import v4_clearer

def v5(game, p):
    acts = game.get_actions(p)
    if not acts: return None
    enemy = 'black' if p == 'red' else 'red'
    flag_pos = (0, 0) if enemy == 'red' else (11, 0)
    my_flag = (0, 0) if p == 'red' else (11, 0)
    barrier_mine = (1, 0) if enemy == 'red' else (10, 0)
    doorway = (2, 0) if enemy == 'red' else (9, 0)
    my_camp = [0, 1, 2, 3, 4] if p == 'red' else [11, 10, 9, 8, 7]

    # 1. Instant Flag Capture
    for a in acts:
        if a['type'] == 'move' and a['to'] == flag_pos: return a

    # 2. Sapper Threat Evacuation
    for a in acts:
        if a['type'] == 'move' and (a['card'].is_sapper or a['card'].is_mochigoma):
            fr = a['from']
            threatened = False
            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nr, nc = fr[0] + dr, fr[1] + dc
                if 0 <= nr < 12 and 0 <= nc < 5:
                    adj = game.board[nr][nc]
                    if adj and adj.player == enemy and not adj.is_flag and not adj.is_landmine:
                        threatened = True; break
            if threatened:
                tr, tc = a['to']
                safe = True
                for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    nr, nc = tr + dr, tc + dc
                    if 0 <= nr < 12 and 0 <= nc < 5:
                        adj = game.board[nr][nc]
                        if adj and adj.player == enemy and not adj.is_flag and not adj.is_landmine:
                            safe = False; break
                if safe: return a

    # 3. Intercept threats in camp or column 0
    for a in acts:
        if a['type'] == 'move' and a['target'] and a['target'].player == enemy:
            tr, tc = a['to']
            c = a['card']
            if not (c.is_sapper or c.is_mochigoma):
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

    enemy_mobiles_col0 = sum(1 for r in range(12) if game.board[r][0] and game.board[r][0].player == enemy and not game.board[r][0].is_immobile)

    # 5. Move Scoring
    for a in acts:
        s = 25
        if a['type'] == 'move':
            fr, fc = a['from']
            tr, tc = a['to']
            c = a['card']
            tgt = a['target']
            my_r = c.rank_val
            is_sapper = c.is_sapper or c.is_mochigoma

            if is_sapper:
                if enemy_mobiles_col0 > 0 and tr in [5, 6] and not (tgt and (tgt.is_landmine or tgt.is_flag)):
                    s -= 500000
                elif enemy_mobiles_col0 == 0:
                    d_bm = abs(tr - barrier_mine[0]) + abs(tc - barrier_mine[1])
                    old_d = abs(fr - barrier_mine[0]) + abs(fc - barrier_mine[1])
                    if d_bm < old_d: s += 70000

            # Sapper never steps adjacent to mobile enemy
            if is_sapper:
                for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    nr, nc = tr + dr, tc + dc
                    if 0 <= nr < 12 and 0 <= nc < 5:
                        adj = game.board[nr][nc]
                        if adj and adj.player == enemy and not adj.is_flag and not adj.is_landmine:
                            s -= 250000

            # Doorway Clearance: non-sapper clears (2,0)/(9,0) so sapper has open highway
            if fr == doorway and not is_sapper:
                if tc != 0: s += 30000
                else: s -= 30000

            if tgt and tgt.player == enemy:
                k = game.memory[p].get(tgt.id)
                if k:
                    if k['is_flag']: return a
                    elif k['is_landmine']: s += (100000 if is_sapper else -500000)
                    elif k['rank_val'] > 0:
                        if c.is_bomb: s += 85000 + k['rank_val'] * 1000
                        elif is_sapper: s = -9999999
                        elif my_r > k['rank_val']: s += 45000 + k['rank_val'] * 500
                        else: s = -9999999
                elif (tr, tc) in game.known_mines[p]: s += (100000 if is_sapper else -500000)
                else:
                    if is_sapper: s -= 50000
                    elif my_r in [2, 3]: s += 4500
                    elif my_r >= 6: s += 3500
                    else: s += 50

            # Heavy officer pushes on Column 0
            if fc == 0 and tc == 0 and (my_r >= 5 or my_r in [2, 3]):
                if (p == 'red' and tr > fr) or (p == 'black' and tr < fr):
                    s += 1300

            # Forward movement
            if p == 'red' and tr > fr: s += 35
            if p == 'black' and tr < fr: s += 35

            if is_sapper:
                d_bm = abs(tr - barrier_mine[0]) + abs(tc - barrier_mine[1])
                old_d = abs(fr - barrier_mine[0]) + abs(fc - barrier_mine[1])
                if d_bm < old_d: s += 6000
        elif a['type'] == 'drop':
            s += 20
        a['s'] = s
    acts.sort(key=lambda x: x['s'], reverse=True)
    return acts[0]

tec.STRAT_REGISTRY['v5'] = v5

print("Testing V5 vs V4_CLEARER (100 games)...")
w, l, d, rate, dt = tec.run_tournament_stage('v5', 'v4_clearer', 1, 1, 100)
print(f"STAGE 5 (V5 vs V4_CLEARER): W={w}, L={l}, D={d}, Decisive Rate={rate:.1f}% in {dt:.1f}s")
