import master_10_ladder as m10

# V6: Hunter-Killer Sapper Protocol with Column 4 Defense
def v6_calib(game, p):
    acts = game.get_actions(p)
    if not acts: return None
    enemy = 'black' if p == 'red' else 'red'
    flag_pos = (0, 0) if enemy == 'red' else (11, 0)
    barrier_mine = (1, 0) if enemy == 'red' else (10, 0)
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

    # 3. Intercept threats in camp or on flank with heavy officers
    for a in acts:
        if a['type'] == 'move' and a['target'] and a['target'].player == enemy:
            tr, tc = a['to']
            c = a['card']
            if not (c.is_sapper or c.is_mochigoma):
                if tr in my_camp or tc in [0, 4]:
                    k = game.memory[p].get(a['target'].id)
                    if c.is_bomb or (k and c.rank_val >= k.get('rank_val', 0)) or (not k and c.rank_val >= 6):
                        return a

    # 4. Deploy starting reserves: row 4/7, prefer col 4
    for a in acts:
        if a['type'] == 'drop' and a['hand'] == 'starting':
            tr, tc = a['to']
            if (p == 'red' and tr == 4 and tc == 4) or (p == 'black' and tr == 7 and tc == 4): return a
    for a in acts:
        if a['type'] == 'drop' and a['hand'] == 'starting':
            tr, tc = a['to']
            if (p == 'red' and tr == 4) or (p == 'black' and tr == 7): return a

    # 5. Hunter-Killer Sapper Vector
    enemy_sapper_pos = None
    for r in range(12):
        for c in range(5):
            ec = game.board[r][c]
            if ec and ec.player == enemy:
                k = game.memory[p].get(ec.id)
                if ec.is_sapper or ec.is_mochigoma or (k and k.get('is_sapper')):
                    enemy_sapper_pos = (r, c); break
        if enemy_sapper_pos: break

    enemy_mobiles_col0 = sum(1 for r in range(12) if game.board[r][0] and game.board[r][0].player == enemy and not game.board[r][0].is_immobile)

    for a in acts:
        s = 30
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
                    if d_bm < old_d: s += 80000

            if is_sapper:
                for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    nr, nc = tr + dr, tc + dc
                    if 0 <= nr < 12 and 0 <= nc < 5:
                        adj = game.board[nr][nc]
                        if adj and adj.player == enemy and not adj.is_flag and not adj.is_landmine:
                            s -= 250000

            # Hunter-Killer
            if enemy_sapper_pos and (my_r >= 6 or c.is_bomb):
                d_es = abs(tr - enemy_sapper_pos[0]) + abs(tc - enemy_sapper_pos[1])
                old_d_es = abs(fr - enemy_sapper_pos[0]) + abs(fc - enemy_sapper_pos[1])
                if d_es < old_d_es: s += 95000

            if tgt and tgt.player == enemy:
                k = game.memory[p].get(tgt.id)
                if k:
                    if k['is_flag']: return a
                    elif k['is_landmine']: s += (100000 if is_sapper else -500000)
                    elif k['rank_val'] > 0:
                        if c.is_bomb: s += 90000 + k['rank_val'] * 1200
                        elif is_sapper: s = -9999999
                        elif my_r > k['rank_val']: s += 50000 + k['rank_val'] * 500
                        else: s = -9999999
                elif (tr, tc) in game.known_mines[p]: s += (100000 if is_sapper else -500000)
                else:
                    if is_sapper: s -= 50000
                    elif my_r in [2, 3]: s += 4500
                    elif my_r >= 6: s += 3500
                    else: s += 50

            # Column 4 push
            if fc == 4 and tc == 4 and my_r >= 6:
                if (p == 'red' and tr > fr) or (p == 'black' and tr < fr): s += 3200

            # Column 0 push
            if fc == 0 and tc == 0 and (my_r >= 5 or my_r in [2, 3]):
                if (p == 'red' and tr > fr) or (p == 'black' and tr < fr): s += 1200

            if p == 'red' and tr > fr: s += 40
            if p == 'black' and tr < fr: s += 40

            if is_sapper:
                d_bm = abs(tr - barrier_mine[0]) + abs(tc - barrier_mine[1])
                old_d = abs(fr - barrier_mine[0]) + abs(fc - barrier_mine[1])
                if d_bm < old_d: s += 8000
        elif a['type'] == 'drop': s += 25
        a['s'] = s
    acts.sort(key=lambda x: x['s'], reverse=True)
    return acts[0]

m10.STRAT_REGISTRY['v6_calib'] = v6_calib

print("Testing V6_CALIB vs V5 (50 games)...")
w, l, d, rate, dt = m10.run_tournament_stage('v6_calib', 'v5', 1, 1, 50)
print(f"Stage 6 (V6_CALIB vs V5): W={w}, L={l}, D={d}, Rate={rate:.1f}%")

# Test Stage 7: V7 vs V6_CALIB
print("\nTesting V7 vs V6_CALIB (50 games)...")
w, l, d, rate, dt = m10.run_tournament_stage('v7', 'v6_calib', 1, 1, 50)
print(f"Stage 7 (V7 vs V6_CALIB): W={w}, L={l}, D={d}, Rate={rate:.1f}%")

# V9 Calibrated: Strong Flank Pincer
def v9_calib(game, p):
    acts = game.get_actions(p)
    if not acts: return None
    enemy = 'black' if p == 'red' else 'red'
    flag_pos = (0, 0) if enemy == 'red' else (11, 0)
    barrier_mine = (1, 0) if enemy == 'red' else (10, 0)
    bunker_rows = [0, 1] if enemy == 'red' else [10, 11]
    my_camp = [0, 1, 2, 3, 4] if p == 'red' else [11, 10, 9, 8, 7]

    for a in acts:
        if a['type'] == 'move' and a['to'] == flag_pos: return a

    intruders = []
    for r in my_camp:
        for c in range(5):
            ec = game.board[r][c]
            if ec and ec.player == enemy:
                intruders.append((r, c, ec))

    if intruders:
        for a in acts:
            if a['type'] == 'move':
                tr, tc = a['to']
                tgt = a['target']
                c = a['card']
                if tgt and tgt.player == enemy and tr in my_camp:
                    k = game.memory[p].get(tgt.id)
                    if c.is_bomb or (k and c.rank_val >= k['rank_val']) or (not k and c.rank_val >= 7):
                        return a
        for a in acts:
            if a['type'] == 'drop':
                dr, dc = a['to']
                for ir, ic, iec in intruders:
                    if abs(dr - ir) + abs(dc - ic) == 1:
                        if a['card'].rank_val >= 7 or a['card'].is_bomb:
                            return a

    for a in acts:
        if a['type'] == 'drop' and a['hand'] == 'starting':
            tr, tc = a['to']
            if (p == 'red' and tr == 4 and tc == 4) or (p == 'black' and tr == 7 and tc == 4): return a
    for a in acts:
        if a['type'] == 'drop' and a['hand'] == 'starting':
            tr, tc = a['to']
            if (p == 'red' and tr == 4) or (p == 'black' and tr == 7): return a

    enemy_sapper_pos = None
    for r in range(12):
        for c in range(5):
            card = game.board[r][c]
            if card and card.player == enemy:
                if card.is_sapper or card.is_mochigoma or (card.id in game.memory[p] and game.memory[p][card.id].get('is_sapper')):
                    enemy_sapper_pos = (r, c); break
        if enemy_sapper_pos: break

    enemy_bombs_dead = sum(1 for c in game.graveyard if c.is_bomb and c.player == enemy)
    ten_is_invincible = (enemy_bombs_dead >= 2)

    for a in acts:
        s = 50
        if a['type'] == 'move':
            fr, fc = a['from']
            tr, tc = a['to']
            c = a['card']
            tgt = a['target']
            my_r = c.rank_val
            is_sapper = c.is_sapper or c.is_mochigoma

            if intruders:
                for ir, ic, iec in intruders:
                    d = abs(tr - ir) + abs(tc - ic)
                    old_d = abs(fr - ir) + abs(fc - ic)
                    if d < old_d and (my_r >= 6 or c.is_bomb):
                        s += 190000

            if enemy_sapper_pos and my_r >= 6:
                d_es = abs(tr - enemy_sapper_pos[0]) + abs(tc - enemy_sapper_pos[1])
                old_d_es = abs(fr - enemy_sapper_pos[0]) + abs(fc - enemy_sapper_pos[1])
                if d_es < old_d_es: s += 120000

            if my_r == 10 and ten_is_invincible:
                if tgt and tgt.player == enemy:
                    if tr in bunker_rows and tc in [0, 1, 2]: s -= 120000
                    else: s += 200000
                else:
                    d_flag = abs(tr - flag_pos[0]) + abs(tc - flag_pos[1])
                    s += (20 - d_flag) * 900
            elif tgt and tgt.player == enemy:
                k = game.memory[p].get(tgt.id)
                if k:
                    if k['is_flag']: return a
                    elif k['is_landmine']: s += (150000 if is_sapper else -500000)
                    elif k['rank_val'] > 0:
                        if c.is_bomb: s += 150000 + k['rank_val'] * 1200
                        elif is_sapper: s = -9999999
                        elif my_r > k['rank_val']: s += 65000 + k['rank_val'] * 600
                        else: s = -9999999
                elif (tr, tc) in game.known_mines[p]: s += (150000 if is_sapper else -500000)
                else:
                    if is_sapper: s -= 40000
                    elif my_r in [2, 3]: s += 2000
                    else: s += 100

            if is_sapper:
                d_bm = abs(tr - barrier_mine[0]) + abs(tc - barrier_mine[1])
                old_d_bm = abs(fr - barrier_mine[0]) + abs(fc - barrier_mine[1])
                if d_bm < old_d_bm: s += 45000

            # STRONG FLANK PINCER PUSH ALONG COLUMN 4
            if fc == 4 and tc == 4 and my_r >= 6:
                if (p == 'red' and tr > fr) or (p == 'black' and tr < fr):
                    s += 4000

            if p == 'red' and tr > fr: s += 50
            if p == 'black' and tr < fr: s += 50
        elif a['type'] == 'drop': s += 35
        a['s'] = s
    acts.sort(key=lambda x: x['s'], reverse=True)
    return acts[0]

m10.STRAT_REGISTRY['v9_calib'] = v9_calib

print("\nTesting V9_CALIB vs V8 (50 games)...")
w, l, d, rate, dt = m10.run_tournament_stage('v9_calib', 'v8', 1, 1, 50)
print(f"Stage 9 (V9_CALIB vs V8): W={w}, L={l}, D={d}, Rate={rate:.1f}%")

print("\nTesting V10 vs V9_CALIB (50 games)...")
w, l, d, rate, dt = m10.run_tournament_stage('v10', 'v9_calib', 1, 1, 50)
print(f"Stage 10 (V10 vs V9_CALIB): W={w}, L={l}, D={d}, Rate={rate:.1f}%")
