import run_grandmaster_tournaments as rgt
import random

# =====================================================================
# CALIBRATED GRANDMASTER 5-TIER STRATEGIES
# =====================================================================

# MODEL 1 (M1): Tactical Memory V1 vs Random V0
# (Already tested: 93.19% win rate -> PASSED)

# MODEL 2 (M2): Bayesian Ambush V2 vs M1
# (Already tested: 100.00% win rate -> PASSED)

# MODEL 3 (M3): Corridor Demolition V3 vs M2
# (Already tested: 100.00% win rate -> PASSED)

# MODEL 4 (M4): Invincible Blitz & Defcon 1 Homeland Defense V4 vs M3
def m4_v4_calibrated(game, p):
    acts = game.get_actions(p)
    if not acts: return None
    enemy = 'black' if p == 'red' else 'red'
    flag_pos = (0, 0) if enemy == 'red' else (11, 0)
    my_flag = (0, 0) if p == 'red' else (11, 0)
    barrier_mine = (1, 0) if enemy == 'red' else (10, 0)
    bunker_rows = [0, 1] if enemy == 'red' else [10, 11]
    my_camp = [0, 1, 2, 3, 4] if p == 'red' else [11, 10, 9, 8, 7]

    # 1. Win in 1
    for a in acts:
        if a['type'] == 'move':
            if a['to'] == flag_pos: return a
            if a['target'] and a['target'].player == enemy and a['target'].is_flag: return a

    # 2. Defcon 1: Kill intruders in our camp immediately!
    for a in acts:
        if a['type'] == 'move':
            tr, tc = a['to']
            tgt = a['target']
            c = a['card']
            if tgt and tgt.player == enemy and tr in my_camp:
                if c.rank_val > 0 or c.is_bomb:
                    k = game.memory[p].get(id(tgt))
                    if not k or c.is_bomb or c.rank_val >= k.get('rank_val', 0):
                        return a

    # 3. Defensive drop adjacent to intruder
    intruders = []
    for r in my_camp:
        for c in range(5):
            ec = game.board[r][c]
            if ec and ec.player == enemy:
                intruders.append((r, c, ec))

    if intruders:
        for a in acts:
            if a['type'] == 'drop':
                dr, dc = a['to']
                for ir, ic, iec in intruders:
                    if abs(dr - ir) + abs(dc - ic) == 1:
                        if a['card'].rank_val >= 7 or a['card'].is_bomb:
                            return a

    # 4. Track enemy sapper
    enemy_sapper_pos = None
    for r in range(12):
        for c in range(5):
            card = game.board[r][c]
            if card and card.player == enemy:
                if card.is_sapper or card.is_mochigoma or (id(card) in game.memory[p] and game.memory[p][id(card)].get('is_sapper')):
                    enemy_sapper_pos = (r, c)
                    break
        if enemy_sapper_pos: break

    enemy_bombs_dead = sum(1 for c in game.graveyard if c.is_bomb and c.player == enemy)
    ten_is_invincible = (enemy_bombs_dead >= 2)

    for a in acts:
        s = 30
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
                    if d < old_d and (my_r >= 5 or c.is_bomb):
                        s += 150000

            if enemy_sapper_pos and my_r >= 5:
                d_es = abs(tr - enemy_sapper_pos[0]) + abs(tc - enemy_sapper_pos[1])
                old_d_es = abs(fr - enemy_sapper_pos[0]) + abs(fc - enemy_sapper_pos[1])
                if d_es < old_d_es:
                    s += 80000

            if tgt and tgt.player == enemy:
                cid = id(tgt)
                k = game.memory[p].get(cid)
                if k:
                    if k['is_flag']: return a
                    elif k['is_landmine']: s += (120000 if is_sapper else -200000)
                    elif k['rank_val'] > 0:
                        if c.is_bomb: s += 100000 + k['rank_val'] * 1500
                        elif is_sapper: s -= 80000
                        elif my_r > k['rank_val']: s += 40000 + k['rank_val'] * 600
                        else: s -= 80000
                elif (tr, tc) in game.known_mines[p]: s += (120000 if is_sapper else -200000)
                else:
                    if tr in bunker_rows and tc in [0, 1, 2]:
                        if is_sapper: s += 80000
                        else: s -= 150000
                    else:
                        if my_r in [2, 3]: s += 2000
                        elif is_sapper: s -= 1000 # Sapper protects itself, doesn't suicide into unknowns!
                        elif my_r >= 8: s += 100

            if my_r == 10 and ten_is_invincible:
                if tgt and tgt.player == enemy:
                    if tr in bunker_rows and tc in [0, 1, 2]: s -= 100000
                    else: s += 90000
                else:
                    d_flag = abs(tr - flag_pos[0]) + abs(tc - flag_pos[1])
                    s += (20 - d_flag) * 400

            if is_sapper:
                d_bm = abs(tr - barrier_mine[0]) + abs(tc - barrier_mine[1])
                old_d_bm = abs(fr - barrier_mine[0]) + abs(fc - barrier_mine[1])
                if d_bm < old_d_bm: s += 35000

            doorway = (2, 0) if enemy == 'red' else (9, 0)
            if fr == doorway and not is_sapper:
                if tc != 0: s += 40000
                else: s -= 40000

            if p == 'red' and tr > fr: s += 45
            if p == 'black' and tr < fr: s += 45

        elif a['type'] == 'drop':
            if p == 'red' and a['to'][0] == 4: s += 200
            elif p == 'black' and a['to'][0] == 7: s += 200
            else: s += 20
        a['s'] = s

    acts.sort(key=lambda x: x['s'], reverse=True)
    return acts[0]

# MODEL 5 (M5): Grandmaster Minimax Equilibrium & Mochigoma Blitzkrieg V5
def m5_v5_calibrated(game, p):
    acts = game.get_actions(p)
    if not acts: return None
    enemy = 'black' if p == 'red' else 'red'
    flag_pos = (0, 0) if enemy == 'red' else (11, 0)
    my_flag = (0, 0) if p == 'red' else (11, 0)
    barrier_mine = (1, 0) if enemy == 'red' else (10, 0)
    bunker_rows = [0, 1] if enemy == 'red' else [10, 11]
    my_camp = [0, 1, 2, 3, 4] if p == 'red' else [11, 10, 9, 8, 7]

    # 1. Instant Mate: Capture Flag
    for a in acts:
        if a['type'] == 'move':
            if a['to'] == flag_pos: return a
            if a['target'] and a['target'].player == enemy and a['target'].is_flag: return a

    # 2. Checkmate Mochigoma Drop: If any cell adjacent to enemy Flag is empty, drop Conscript for mate!
    adj_flag = [(flag_pos[0]+1, flag_pos[1]), (flag_pos[0], flag_pos[1]+1)] if enemy == 'red' else [(flag_pos[0]-1, flag_pos[1]), (flag_pos[0], flag_pos[1]+1)]
    for a in acts:
        if a['type'] == 'drop' and a['to'] in adj_flag:
            return a

    # 3. Defcon 1: Emergency Interception of Intruder in Camp
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
                    if c.rank_val > 0 or c.is_bomb:
                        k = game.memory[p].get(id(tgt))
                        if not k or c.is_bomb or c.rank_val >= k.get('rank_val', 0):
                            return a
        for a in acts:
            if a['type'] == 'drop':
                dr, dc = a['to']
                for ir, ic, iec in intruders:
                    if abs(dr - ir) + abs(dc - ic) == 1:
                        if a['card'].rank_val >= 7 or a['card'].is_bomb:
                            return a

    # 4. Enemy Sapper Tracking
    enemy_sapper_pos = None
    for r in range(12):
        for c in range(5):
            card = game.board[r][c]
            if card and card.player == enemy:
                if card.is_sapper or card.is_mochigoma or (id(card) in game.memory[p] and game.memory[p][id(card)].get('is_sapper')):
                    enemy_sapper_pos = (r, c)
                    break
        if enemy_sapper_pos: break

    enemy_bombs_dead = sum(1 for c in game.graveyard if c.is_bomb and c.player == enemy)
    ten_is_invincible = (enemy_bombs_dead >= 2)

    # Count enemy officers remaining
    enemy_officers = [c for r in game.board for c in r if c and c.player == enemy and c.rank_val > 0]
    sweep_mode = (len(enemy_officers) <= 4)

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
                        s += 200000

            if enemy_sapper_pos and my_r >= 6:
                d_es = abs(tr - enemy_sapper_pos[0]) + abs(tc - enemy_sapper_pos[1])
                old_d_es = abs(fr - enemy_sapper_pos[0]) + abs(fc - enemy_sapper_pos[1])
                if d_es < old_d_es:
                    s += 120000

            # Invincible Sweeper: Ten moves aggressively forward
            if my_r == 10 and ten_is_invincible:
                if tgt and tgt.player == enemy:
                    if tr in bunker_rows and tc in [0, 1, 2]: s -= 120000
                    else: s += 200000
                else:
                    d_flag = abs(tr - flag_pos[0]) + abs(tc - flag_pos[1])
                    s += (20 - d_flag) * 1000

            # General Sweeper when enemy is depleted
            elif sweep_mode and my_r >= 7:
                if tgt and tgt.player == enemy:
                    s += 150000
                else:
                    d_flag = abs(tr - flag_pos[0]) + abs(tc - flag_pos[1])
                    s += (20 - d_flag) * 500

            elif tgt and tgt.player == enemy:
                cid = id(tgt)
                k = game.memory[p].get(cid)
                if k:
                    if k['is_flag']: return a
                    elif k['is_landmine']: s += (160000 if is_sapper else -250000)
                    elif k['rank_val'] > 0:
                        if c.is_bomb: s += 170000 + k['rank_val'] * 2000
                        elif is_sapper: s -= 100000
                        elif my_r > k['rank_val']: s += 80000 + k['rank_val'] * 800
                        else: s -= 100000
                elif (tr, tc) in game.known_mines[p]: s += (160000 if is_sapper else -250000)
                else:
                    if tr in bunker_rows and tc in [0, 1, 2]:
                        if is_sapper: s += 140000
                        else: s -= 200000
                    else:
                        if my_r in [2, 3]: s += 3000
                        elif is_sapper: s -= 5000 # Sapper strictly avoids attacking face-down unknowns!
                        elif my_r >= 8: s += 200

            # 3-Ply Threat Evasion
            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nr, nc = tr + dr, tc + dc
                if 0 <= nr < 12 and 0 <= nc < 5:
                    adj = game.board[nr][nc]
                    if adj and adj.player == enemy:
                        k_adj = game.memory[p].get(id(adj))
                        if k_adj:
                            if k_adj.get('rank_val', 0) > my_r: s -= 25000
                            elif k_adj.get('is_bomb') and my_r >= 7: s -= 40000

            # Sapper pathing to barrier mine
            if is_sapper:
                d_bm = abs(tr - barrier_mine[0]) + abs(tc - barrier_mine[1])
                old_d_bm = abs(fr - barrier_mine[0]) + abs(fc - barrier_mine[1])
                if d_bm < old_d_bm: s += 50000

            # Doorway Clearance
            doorway = (2, 0) if enemy == 'red' else (9, 0)
            if fr == doorway and not is_sapper:
                if tc != 0: s += 50000
                else: s -= 50000

            # Sapper Escort Protocol: Higher officer (8, 9, 10) marches 1 step ahead of Sapper on Column 0
            if fc == 0 and tc == 0 and my_r >= 8:
                d_bm = abs(tr - barrier_mine[0])
                old_d_bm = abs(fr - barrier_mine[0])
                if d_bm < old_d_bm and d_bm >= 2:
                    s += 40000

            # Flank push
            if fc == 4 and tc == 4 and my_r >= 7:
                if (p == 'red' and tr > fr) or (p == 'black' and tr < fr):
                    s += 250

            if p == 'red' and tr > fr: s += 60
            if p == 'black' and tr < fr: s += 60

        elif a['type'] == 'drop':
            tr, tc = a['to']
            c = a['card']
            # Forward offensive drop: drop conscripts into enemy flank
            if (p == 'red' and tr == 4) or (p == 'black' and tr == 7):
                s += 800
            elif tc in [0, 4]:
                s += 500
            else:
                s += 200
        a['s'] = s

    acts.sort(key=lambda x: x['s'], reverse=True)
    return acts[0]

rgt.STRAT_REGISTRY['m4_v4'] = m4_v4_calibrated
rgt.STRAT_REGISTRY['m5_v5'] = m5_v5_calibrated

print("=" * 80)
print("STAGE 4: M4 (Calibrated V4) vs M3 (V3) [1000 Games]")
w_new, w_old, draws, rate, dt = rgt.run_tournament_stage('m4_v4', 'm3_v3', 1, 1, 1000)
print(f"M4 Wins={w_new} | M3 Wins={w_old} | Draws={draws} | Win Rate={rate:.2f}% ({dt:.1f}s)")

print("\nSTAGE 5: M5 (Calibrated V5) vs M4 (V4) [1000 Games]")
w_new, w_old, draws, rate, dt = rgt.run_tournament_stage('m5_v5', 'm4_v4', 1, 1, 1000)
print(f"M5 Wins={w_new} | M4 Wins={w_old} | Draws={draws} | Win Rate={rate:.2f}% ({dt:.1f}s)")
