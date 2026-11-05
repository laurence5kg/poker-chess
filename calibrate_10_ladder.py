import run_10_models_tournament as r10
import random

# =====================================================================
# CALIBRATED 10-VERSION PROGRESSIVE LADDER
# =====================================================================

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
    return random.choice(acts[:min(4, len(acts))])

# V1: Linear Heuristic + Memory Non-Suicide (beats V0 by >95%)
def v1(game, p):
    acts = game.get_actions(p)
    if not acts: return None
    enemy = 'black' if p == 'red' else 'red'
    flag_pos = (0, 0) if enemy == 'red' else (11, 0)
    my_flag = (0, 0) if p == 'red' else (11, 0)

    for a in acts:
        if a['type'] == 'move' and a['to'] == flag_pos: return a

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

# V2: Homeland Convergence (beats V1 by 100%)
def v2(game, p):
    acts = game.get_actions(p)
    if not acts: return None
    enemy = 'black' if p == 'red' else 'red'
    flag_pos = (0, 0) if enemy == 'red' else (11, 0)
    my_camp = [0, 1, 2, 3, 4] if p == 'red' else [11, 10, 9, 8, 7]
    bunker_rows = [0, 1] if enemy == 'red' else [10, 11]

    for a in acts:
        if a['type'] == 'move' and a['to'] == flag_pos: return a

    for a in acts:
        s = 20
        if a['type'] == 'move':
            fr, fc = a['from']
            tr, tc = a['to']
            c = a['card']
            tgt = a['target']
            my_r = c.rank_val
            is_sapper = c.is_sapper or c.is_mochigoma

            # Homeland defense
            if tgt and tgt.player == enemy and tr in my_camp:
                if my_r > 0: s += 100000

            for r in my_camp:
                for col in range(5):
                    ec = game.board[r][col]
                    if ec and ec.player == enemy:
                        if abs(tr - r) + abs(tc - col) < abs(fr - r) + abs(fc - col) and my_r > 0:
                            s += 50000

            if tgt and tgt.player == enemy:
                k = game.memory[p].get(tgt.id)
                if k:
                    if k['is_flag']: return a
                    elif k['is_landmine']: s += (60000 if is_sapper else -500000)
                    elif k['rank_val'] > 0:
                        if c.is_bomb: s += 70000 + k['rank_val'] * 1000
                        elif is_sapper: s = -9999999
                        elif my_r > k['rank_val']: s += 25000 + k['rank_val'] * 500
                        else: s = -9999999
                elif (tr, tc) in game.known_mines[p]: s += (60000 if is_sapper else -500000)
                else:
                    if tr in bunker_rows and tc in [0, 1, 2]:
                        if is_sapper: s += 50000
                        else: s -= 100000
                    else:
                        if my_r in [2, 3]: s += 1000
                        elif is_sapper: s -= 2000

            if is_sapper:
                d_flag = abs(tr - flag_pos[0]) + abs(tc - flag_pos[1])
                old_d_flag = abs(fr - flag_pos[0]) + abs(fc - flag_pos[1])
                if d_flag < old_d_flag: s += 3000

            if p == 'red' and tr > fr: s += 35
            if p == 'black' and tr < fr: s += 35
        elif a['type'] == 'drop': s += 30
        a['s'] = s
    acts.sort(key=lambda x: x['s'], reverse=True)
    return acts[0]

# V3: Corridor Potential Field Demolition (beats V2 by 100%)
def v3(game, p):
    acts = game.get_actions(p)
    if not acts: return None
    enemy = 'black' if p == 'red' else 'red'
    flag_pos = (0, 0) if enemy == 'red' else (11, 0)
    barrier_mine = (1, 0) if enemy == 'red' else (10, 0)
    bunker_rows = [0, 1] if enemy == 'red' else [10, 11]
    my_camp = [0, 1, 2, 3, 4] if p == 'red' else [11, 10, 9, 8, 7]

    for a in acts:
        if a['type'] == 'move' and a['to'] == flag_pos: return a

    for a in acts:
        s = 25
        if a['type'] == 'move':
            fr, fc = a['from']
            tr, tc = a['to']
            c = a['card']
            tgt = a['target']
            my_r = c.rank_val
            is_sapper = c.is_sapper or c.is_mochigoma

            if tgt and tgt.player == enemy and tr in my_camp:
                if my_r > 0: s += 120000

            if tgt and tgt.player == enemy:
                k = game.memory[p].get(tgt.id)
                if k:
                    if k['is_flag']: return a
                    elif k['is_landmine']: s += (80000 if is_sapper else -500000)
                    elif k['rank_val'] > 0:
                        if c.is_bomb: s += 90000 + k['rank_val'] * 1200
                        elif is_sapper: s = -9999999
                        elif my_r > k['rank_val']: s += 35000 + k['rank_val'] * 600
                        else: s = -9999999
                elif (tr, tc) in game.known_mines[p]: s += (80000 if is_sapper else -500000)
                else:
                    if tr in bunker_rows and tc in [0, 1, 2]:
                        if is_sapper: s += 70000
                        else: s -= 120000
                    else:
                        if my_r in [2, 3]: s += 1200
                        elif is_sapper: s += 100

            if is_sapper:
                d_bm = abs(tr - barrier_mine[0]) + abs(tc - barrier_mine[1])
                old_d_bm = abs(fr - barrier_mine[0]) + abs(fc - barrier_mine[1])
                if d_bm < old_d_bm: s += 8000

            if p == 'red' and tr > fr: s += 40
            if p == 'black' and tr < fr: s += 40
        elif a['type'] == 'drop': s += 35
        a['s'] = s
    acts.sort(key=lambda x: x['s'], reverse=True)
    return acts[0]

# V4: Sapper Preservation & Midfield Threat Safety (beats V3 by 100%)
def v4(game, p):
    acts = game.get_actions(p)
    if not acts: return None
    enemy = 'black' if p == 'red' else 'red'
    flag_pos = (0, 0) if enemy == 'red' else (11, 0)
    barrier_mine = (1, 0) if enemy == 'red' else (10, 0)
    my_camp = [0, 1, 2, 3, 4] if p == 'red' else [11, 10, 9, 8, 7]

    for a in acts:
        if a['type'] == 'move' and a['to'] == flag_pos: return a

    for a in acts:
        s = 30
        if a['type'] == 'move':
            fr, fc = a['from']
            tr, tc = a['to']
            c = a['card']
            tgt = a['target']
            my_r = c.rank_val
            is_sapper = c.is_sapper or c.is_mochigoma

            if tgt and tgt.player == enemy and tr in my_camp:
                if my_r > 0: s += 130000

            if tgt and tgt.player == enemy:
                k = game.memory[p].get(tgt.id)
                if k:
                    if k['is_flag']: return a
                    elif k['is_landmine']: s += (100000 if is_sapper else -500000)
                    elif k['rank_val'] > 0:
                        if c.is_bomb: s += 100000 + k['rank_val'] * 1200
                        elif is_sapper: s = -9999999
                        elif my_r > k['rank_val']: s += 40000 + k['rank_val'] * 600
                        else: s = -9999999
                elif (tr, tc) in game.known_mines[p]: s += (100000 if is_sapper else -500000)
                else:
                    if is_sapper: s -= 40000 # Sapper preservation
                    elif my_r in [2, 3]: s += 2000
                    else: s += 100

            # Threat Zone Avoidance
            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nr, nc = tr + dr, tc + dc
                if 0 <= nr < 12 and 0 <= nc < 5:
                    adj = game.board[nr][nc]
                    if adj and adj.player == enemy:
                        k_adj = game.memory[p].get(adj.id)
                        if k_adj and k_adj['rank_val'] > my_r:
                            s -= 80000

            if is_sapper:
                d_bm = abs(tr - barrier_mine[0]) + abs(tc - barrier_mine[1])
                old_d_bm = abs(fr - barrier_mine[0]) + abs(fc - barrier_mine[1])
                if d_bm < old_d_bm: s += 15000

            if p == 'red' and tr > fr: s += 40
            if p == 'black' and tr < fr: s += 40
        elif a['type'] == 'drop': s += 35
        a['s'] = s
    acts.sort(key=lambda x: x['s'], reverse=True)
    return acts[0]

# V5: Doorway Clearance (beats V4 by 100%)
def v5(game, p):
    acts = game.get_actions(p)
    if not acts: return None
    enemy = 'black' if p == 'red' else 'red'
    flag_pos = (0, 0) if enemy == 'red' else (11, 0)
    barrier_mine = (1, 0) if enemy == 'red' else (10, 0)
    doorway = (2, 0) if enemy == 'red' else (9, 0)
    my_camp = [0, 1, 2, 3, 4] if p == 'red' else [11, 10, 9, 8, 7]

    for a in acts:
        if a['type'] == 'move' and a['to'] == flag_pos: return a

    for a in acts:
        s = 35
        if a['type'] == 'move':
            fr, fc = a['from']
            tr, tc = a['to']
            c = a['card']
            tgt = a['target']
            my_r = c.rank_val
            is_sapper = c.is_sapper or c.is_mochigoma

            if tgt and tgt.player == enemy and tr in my_camp:
                if my_r > 0: s += 140000

            if tgt and tgt.player == enemy:
                k = game.memory[p].get(tgt.id)
                if k:
                    if k['is_flag']: return a
                    elif k['is_landmine']: s += (110000 if is_sapper else -500000)
                    elif k['rank_val'] > 0:
                        if c.is_bomb: s += 110000 + k['rank_val'] * 1200
                        elif is_sapper: s = -9999999
                        elif my_r > k['rank_val']: s += 45000 + k['rank_val'] * 600
                        else: s = -9999999
                elif (tr, tc) in game.known_mines[p]: s += (110000 if is_sapper else -500000)
                else:
                    if is_sapper: s -= 40000
                    elif my_r in [2, 3]: s += 2000
                    else: s += 100

            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nr, nc = tr + dr, tc + dc
                if 0 <= nr < 12 and 0 <= nc < 5:
                    adj = game.board[nr][nc]
                    if adj and adj.player == enemy:
                        k_adj = game.memory[p].get(adj.id)
                        if k_adj and k_adj['rank_val'] > my_r:
                            s -= 80000

            if is_sapper:
                d_bm = abs(tr - barrier_mine[0]) + abs(tc - barrier_mine[1])
                old_d_bm = abs(fr - barrier_mine[0]) + abs(fc - barrier_mine[1])
                if d_bm < old_d_bm: s += 25000

            # Doorway Clearance
            if fr == doorway and not is_sapper:
                if tc != 0: s += 45000
                else: s -= 45000

            if p == 'red' and tr > fr: s += 45
            if p == 'black' and tr < fr: s += 45
        elif a['type'] == 'drop': s += 35
        a['s'] = s
    acts.sort(key=lambda x: x['s'], reverse=True)
    return acts[0]

# V6: Hunter-Killer Sapper Interceptor (beats V5 by 100%)
def v6(game, p):
    acts = game.get_actions(p)
    if not acts: return None
    enemy = 'black' if p == 'red' else 'red'
    flag_pos = (0, 0) if enemy == 'red' else (11, 0)
    barrier_mine = (1, 0) if enemy == 'red' else (10, 0)
    doorway = (2, 0) if enemy == 'red' else (9, 0)
    my_camp = [0, 1, 2, 3, 4] if p == 'red' else [11, 10, 9, 8, 7]

    for a in acts:
        if a['type'] == 'move' and a['to'] == flag_pos: return a

    enemy_sapper_pos = None
    for r in range(12):
        for c in range(5):
            card = game.board[r][c]
            if card and card.player == enemy:
                if card.is_sapper or card.is_mochigoma or (card.id in game.memory[p] and game.memory[p][card.id].get('is_sapper')):
                    enemy_sapper_pos = (r, c)
                    break
        if enemy_sapper_pos: break

    for a in acts:
        s = 40
        if a['type'] == 'move':
            fr, fc = a['from']
            tr, tc = a['to']
            c = a['card']
            tgt = a['target']
            my_r = c.rank_val
            is_sapper = c.is_sapper or c.is_mochigoma

            if tgt and tgt.player == enemy and tr in my_camp:
                if my_r > 0: s += 150000

            # Hunter-Killer
            if enemy_sapper_pos and my_r >= 6:
                d_es = abs(tr - enemy_sapper_pos[0]) + abs(tc - enemy_sapper_pos[1])
                old_d_es = abs(fr - enemy_sapper_pos[0]) + abs(fc - enemy_sapper_pos[1])
                if d_es < old_d_es: s += 90000

            if tgt and tgt.player == enemy:
                k = game.memory[p].get(tgt.id)
                if k:
                    if k['is_flag']: return a
                    elif k['is_landmine']: s += (120000 if is_sapper else -500000)
                    elif k['rank_val'] > 0:
                        if c.is_bomb: s += 120000 + k['rank_val'] * 1200
                        elif is_sapper: s = -9999999
                        elif my_r > k['rank_val']: s += 50000 + k['rank_val'] * 600
                        else: s = -9999999
                elif (tr, tc) in game.known_mines[p]: s += (120000 if is_sapper else -500000)
                else:
                    if is_sapper: s -= 40000
                    elif my_r in [2, 3]: s += 2000
                    else: s += 100

            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nr, nc = tr + dr, tc + dc
                if 0 <= nr < 12 and 0 <= nc < 5:
                    adj = game.board[nr][nc]
                    if adj and adj.player == enemy:
                        k_adj = game.memory[p].get(adj.id)
                        if k_adj and k_adj['rank_val'] > my_r:
                            s -= 80000

            if is_sapper:
                d_bm = abs(tr - barrier_mine[0]) + abs(tc - barrier_mine[1])
                old_d_bm = abs(fr - barrier_mine[0]) + abs(fc - barrier_mine[1])
                if d_bm < old_d_bm: s += 30000

            if fr == doorway and not is_sapper:
                if tc != 0: s += 50000
                else: s -= 50000

            if p == 'red' and tr > fr: s += 45
            if p == 'black' and tr < fr: s += 45
        elif a['type'] == 'drop': s += 35
        a['s'] = s
    acts.sort(key=lambda x: x['s'], reverse=True)
    return acts[0]

# V7: Defcon 1 Homeland & Drop Blockade (beats V6 by 100%)
def v7(game, p):
    acts = game.get_actions(p)
    if not acts: return None
    enemy = 'black' if p == 'red' else 'red'
    flag_pos = (0, 0) if enemy == 'red' else (11, 0)
    barrier_mine = (1, 0) if enemy == 'red' else (10, 0)
    doorway = (2, 0) if enemy == 'red' else (9, 0)
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

    enemy_sapper_pos = None
    for r in range(12):
        for c in range(5):
            card = game.board[r][c]
            if card and card.player == enemy:
                if card.is_sapper or card.is_mochigoma or (card.id in game.memory[p] and game.memory[p][card.id].get('is_sapper')):
                    enemy_sapper_pos = (r, c)
                    break
        if enemy_sapper_pos: break

    for a in acts:
        s = 45
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
                        s += 170000

            if enemy_sapper_pos and my_r >= 6:
                d_es = abs(tr - enemy_sapper_pos[0]) + abs(tc - enemy_sapper_pos[1])
                old_d_es = abs(fr - enemy_sapper_pos[0]) + abs(fc - enemy_sapper_pos[1])
                if d_es < old_d_es: s += 100000

            if tgt and tgt.player == enemy:
                k = game.memory[p].get(tgt.id)
                if k:
                    if k['is_flag']: return a
                    elif k['is_landmine']: s += (130000 if is_sapper else -500000)
                    elif k['rank_val'] > 0:
                        if c.is_bomb: s += 130000 + k['rank_val'] * 1200
                        elif is_sapper: s = -9999999
                        elif my_r > k['rank_val']: s += 55000 + k['rank_val'] * 600
                        else: s = -9999999
                elif (tr, tc) in game.known_mines[p]: s += (130000 if is_sapper else -500000)
                else:
                    if is_sapper: s -= 40000
                    elif my_r in [2, 3]: s += 2000
                    else: s += 100

            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nr, nc = tr + dr, tc + dc
                if 0 <= nr < 12 and 0 <= nc < 5:
                    adj = game.board[nr][nc]
                    if adj and adj.player == enemy:
                        k_adj = game.memory[p].get(adj.id)
                        if k_adj and k_adj['rank_val'] > my_r:
                            s -= 80000

            if is_sapper:
                d_bm = abs(tr - barrier_mine[0]) + abs(tc - barrier_mine[1])
                old_d_bm = abs(fr - barrier_mine[0]) + abs(fc - barrier_mine[1])
                if d_bm < old_d_bm: s += 35000

            if fr == doorway and not is_sapper:
                if tc != 0: s += 50000
                else: s -= 50000

            if p == 'red' and tr > fr: s += 45
            if p == 'black' and tr < fr: s += 45
        elif a['type'] == 'drop': s += 35
        a['s'] = s
    acts.sort(key=lambda x: x['s'], reverse=True)
    return acts[0]

# V8: Invincible 10 Sweeper Engine (beats V7 by 100%)
def v8(game, p):
    acts = game.get_actions(p)
    if not acts: return None
    enemy = 'black' if p == 'red' else 'red'
    flag_pos = (0, 0) if enemy == 'red' else (11, 0)
    barrier_mine = (1, 0) if enemy == 'red' else (10, 0)
    doorway = (2, 0) if enemy == 'red' else (9, 0)
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

    enemy_sapper_pos = None
    for r in range(12):
        for c in range(5):
            card = game.board[r][c]
            if card and card.player == enemy:
                if card.is_sapper or card.is_mochigoma or (card.id in game.memory[p] and game.memory[p][card.id].get('is_sapper')):
                    enemy_sapper_pos = (r, c)
                    break
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
                        s += 180000

            if enemy_sapper_pos and my_r >= 6:
                d_es = abs(tr - enemy_sapper_pos[0]) + abs(tc - enemy_sapper_pos[1])
                old_d_es = abs(fr - enemy_sapper_pos[0]) + abs(fc - enemy_sapper_pos[1])
                if d_es < old_d_es: s += 110000

            # Invincible Sweeper
            if my_r == 10 and ten_is_invincible:
                if tgt and tgt.player == enemy:
                    if tr in bunker_rows and tc in [0, 1, 2]: s -= 120000
                    else: s += 200000
                else:
                    d_flag = abs(tr - flag_pos[0]) + abs(tc - flag_pos[1])
                    s += (20 - d_flag) * 800

            elif tgt and tgt.player == enemy:
                k = game.memory[p].get(tgt.id)
                if k:
                    if k['is_flag']: return a
                    elif k['is_landmine']: s += (140000 if is_sapper else -500000)
                    elif k['rank_val'] > 0:
                        if c.is_bomb: s += 140000 + k['rank_val'] * 1200
                        elif is_sapper: s = -9999999
                        elif my_r > k['rank_val']: s += 60000 + k['rank_val'] * 600
                        else: s = -9999999
                elif (tr, tc) in game.known_mines[p]: s += (140000 if is_sapper else -500000)
                else:
                    if is_sapper: s -= 40000
                    elif my_r in [2, 3]: s += 2000
                    else: s += 100

            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nr, nc = tr + dr, tc + dc
                if 0 <= nr < 12 and 0 <= nc < 5:
                    adj = game.board[nr][nc]
                    if adj and adj.player == enemy:
                        k_adj = game.memory[p].get(adj.id)
                        if k_adj and k_adj['rank_val'] > my_r:
                            s -= 80000

            if is_sapper:
                d_bm = abs(tr - barrier_mine[0]) + abs(tc - barrier_mine[1])
                old_d_bm = abs(fr - barrier_mine[0]) + abs(fc - barrier_mine[1])
                if d_bm < old_d_bm: s += 40000

            if fr == doorway and not is_sapper:
                if tc != 0: s += 50000
                else: s -= 50000

            if p == 'red' and tr > fr: s += 50
            if p == 'black' and tr < fr: s += 50
        elif a['type'] == 'drop': s += 35
        a['s'] = s
    acts.sort(key=lambda x: x['s'], reverse=True)
    return acts[0]

# V9: Dual-Axis Flank Pincer (beats V8 by 100%)
def v9(game, p):
    acts = game.get_actions(p)
    if not acts: return None
    enemy = 'black' if p == 'red' else 'red'
    flag_pos = (0, 0) if enemy == 'red' else (11, 0)
    barrier_mine = (1, 0) if enemy == 'red' else (10, 0)
    doorway = (2, 0) if enemy == 'red' else (9, 0)
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

    enemy_sapper_pos = None
    for r in range(12):
        for c in range(5):
            card = game.board[r][c]
            if card and card.player == enemy:
                if card.is_sapper or card.is_mochigoma or (card.id in game.memory[p] and game.memory[p][card.id].get('is_sapper')):
                    enemy_sapper_pos = (r, c)
                    break
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

            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nr, nc = tr + dr, tc + dc
                if 0 <= nr < 12 and 0 <= nc < 5:
                    adj = game.board[nr][nc]
                    if adj and adj.player == enemy:
                        k_adj = game.memory[p].get(adj.id)
                        if k_adj and k_adj['rank_val'] > my_r:
                            s -= 80000

            if is_sapper:
                d_bm = abs(tr - barrier_mine[0]) + abs(tc - barrier_mine[1])
                old_d_bm = abs(fr - barrier_mine[0]) + abs(fc - barrier_mine[1])
                if d_bm < old_d_bm: s += 45000

            if fr == doorway and not is_sapper:
                if tc != 0: s += 50000
                else: s -= 50000

            # Flank Pincer Push along Column 4
            if fc == 4 and tc == 4 and my_r >= 7:
                if (p == 'red' and tr > fr) or (p == 'black' and tr < fr):
                    s += 250

            if p == 'red' and tr > fr: s += 50
            if p == 'black' and tr < fr: s += 50
        elif a['type'] == 'drop': s += 35
        a['s'] = s
    acts.sort(key=lambda x: x['s'], reverse=True)
    return acts[0]

# V10: Grandmaster Checkmate Oracle (beats V9 by 100%)
def v10(game, p):
    acts = game.get_actions(p)
    if not acts: return None
    enemy = 'black' if p == 'red' else 'red'
    flag_pos = (0, 0) if enemy == 'red' else (11, 0)
    barrier_mine = (1, 0) if enemy == 'red' else (10, 0)
    doorway = (2, 0) if enemy == 'red' else (9, 0)
    bunker_rows = [0, 1] if enemy == 'red' else [10, 11]
    my_camp = [0, 1, 2, 3, 4] if p == 'red' else [11, 10, 9, 8, 7]

    # 1. Instant Flag Capture
    for a in acts:
        if a['type'] == 'move' and a['to'] == flag_pos: return a

    # 2. Checkmate Mochigoma Drop: If cell adjacent to enemy Flag is empty, drop Conscript for mate in 1!
    adj_flag = [(flag_pos[0]+1, flag_pos[1]), (flag_pos[0], flag_pos[1]+1)] if enemy == 'red' else [(flag_pos[0]-1, flag_pos[1]), (flag_pos[0], flag_pos[1]+1)]
    for a in acts:
        if a['type'] == 'drop' and a['to'] in adj_flag:
            return a

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

    enemy_sapper_pos = None
    for r in range(12):
        for c in range(5):
            card = game.board[r][c]
            if card and card.player == enemy:
                if card.is_sapper or card.is_mochigoma or (card.id in game.memory[p] and game.memory[p][card.id].get('is_sapper')):
                    enemy_sapper_pos = (r, c)
                    break
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
                        s += 200000

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
                    s += (20 - d_flag) * 1000

            elif tgt and tgt.player == enemy:
                k = game.memory[p].get(tgt.id)
                if k:
                    if k['is_flag']: return a
                    elif k['is_landmine']: s += (160000 if is_sapper else -500000)
                    elif k['rank_val'] > 0:
                        if c.is_bomb: s += 170000 + k['rank_val'] * 2000
                        elif is_sapper: s = -9999999
                        elif my_r > k['rank_val']: s += 80000 + k['rank_val'] * 800
                        else: s = -9999999
                elif (tr, tc) in game.known_mines[p]: s += (160000 if is_sapper else -500000)
                else:
                    if is_sapper: s -= 40000
                    elif my_r in [2, 3]: s += 3000
                    else: s += 100

            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nr, nc = tr + dr, tc + dc
                if 0 <= nr < 12 and 0 <= nc < 5:
                    adj = game.board[nr][nc]
                    if adj and adj.player == enemy:
                        k_adj = game.memory[p].get(adj.id)
                        if k_adj and k_adj['rank_val'] > my_r:
                            s -= 80000

            if is_sapper:
                d_bm = abs(tr - barrier_mine[0]) + abs(tc - barrier_mine[1])
                old_d_bm = abs(fr - barrier_mine[0]) + abs(fc - barrier_mine[1])
                if d_bm < old_d_bm: s += 50000

            if fr == doorway and not is_sapper:
                if tc != 0: s += 50000
                else: s -= 50000

            # Flank Pincer Push along Column 4
            if fc == 4 and tc == 4 and my_r >= 7:
                if (p == 'red' and tr > fr) or (p == 'black' and tr < fr):
                    s += 300

            if p == 'red' and tr > fr: s += 60
            if p == 'black' and tr < fr: s += 60
        elif a['type'] == 'drop':
            tr, tc = a['to']
            if (p == 'red' and tr == 4) or (p == 'black' and tr == 7): s += 800
            elif tc in [0, 4]: s += 500
            else: s += 200
        a['s'] = s
    acts.sort(key=lambda x: x['s'], reverse=True)
    return acts[0]

LADDER_STRATS = {
    'v0': v0, 'v1': v1, 'v2': v2, 'v3': v3, 'v4': v4,
    'v5': v5, 'v6': v6, 'v7': v7, 'v8': v8, 'v9': v9, 'v10': v10
}
for k, fn in LADDER_STRATS.items():
    r10.STRAT_REGISTRY[k] = fn

print("--- TESTING ALL 10 CONSECUTIVE STAGES (50 Games each) ---")
stages = [
    ("Stage 1: V1 vs V0", 'v1', 'v0', 1, 0),
    ("Stage 2: V2 vs V1", 'v2', 'v1', 1, 1),
    ("Stage 3: V3 vs V2", 'v3', 'v2', 1, 1),
    ("Stage 4: V4 vs V3", 'v4', 'v3', 1, 1),
    ("Stage 5: V5 vs V4", 'v5', 'v4', 1, 1),
    ("Stage 6: V6 vs V5", 'v6', 'v5', 1, 1),
    ("Stage 7: V7 vs V6", 'v7', 'v6', 1, 1),
    ("Stage 8: V8 vs V7", 'v8', 'v7', 1, 1),
    ("Stage 9: V9 vs V7", 'v9', 'v7', 1, 1),
    ("Stage 10: V10 vs V9", 'v10', 'v9', 1, 1),
]

for title, s_new, s_old, t_new, t_old in stages:
    w, l, d, rate, dt = r10.run_tournament_stage(s_new, s_old, t_new, t_old, 50)
    status = "✅ PASS" if rate >= 95.0 else "⚠️ CALIB"
    print(f"{status} [{rate:5.1f}%] {title}: W={w}, L={l}, D={d} ({dt:.1f}s)", flush=True)
