import run_grandmaster_tournaments as rgt
from test_m4_improvement import m4_upgraded

def m5_grandmaster_v2(game, p):
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

    # 2. Mochigoma Checkmate Drop: If any cell adjacent to enemy Flag is empty, drop Conscript for mate!
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

    for a in acts:
        s = 50
        if a['type'] == 'move':
            fr, fc = a['from']
            tr, tc = a['to']
            c = a['card']
            tgt = a['target']
            my_r = c.rank_val
            is_sapper = c.is_sapper or c.is_mochigoma

            # Defend Camp against intruders
            if intruders:
                for ir, ic, iec in intruders:
                    d = abs(tr - ir) + abs(tc - ic)
                    old_d = abs(fr - ir) + abs(fc - ic)
                    if d < old_d and (my_r >= 6 or c.is_bomb):
                        s += 200000

            # Hunt enemy Sapper
            if enemy_sapper_pos and my_r >= 6:
                d_es = abs(tr - enemy_sapper_pos[0]) + abs(tc - enemy_sapper_pos[1])
                old_d_es = abs(fr - enemy_sapper_pos[0]) + abs(fc - enemy_sapper_pos[1])
                if d_es < old_d_es:
                    s += 95000

            # Invincible Sweeper: Ten moves aggressively forward to crush enemy officers
            if my_r == 10 and ten_is_invincible:
                if tgt and tgt.player == enemy:
                    if tr in bunker_rows and tc in [0, 1, 2]: s -= 120000
                    else: s += 180000
                else:
                    d_flag = abs(tr - flag_pos[0]) + abs(tc - flag_pos[1])
                    s += (20 - d_flag) * 800

            # Combat evaluation
            elif tgt and tgt.player == enemy:
                cid = id(tgt)
                k = game.memory[p].get(cid)
                if k:
                    if k['is_flag']: return a
                    elif k['is_landmine']: s += (150000 if is_sapper else -250000)
                    elif k['rank_val'] > 0:
                        if c.is_bomb: s += 160000 + k['rank_val'] * 2000
                        elif is_sapper: s -= 100000
                        elif my_r > k['rank_val']: s += 70000 + k['rank_val'] * 800
                        else: s -= 100000
                elif (tr, tc) in game.known_mines[p]: s += (150000 if is_sapper else -250000)
                else:
                    if tr in bunker_rows and tc in [0, 1, 2]:
                        if is_sapper: s += 120000
                        else: s -= 200000
                    else:
                        if my_r in [2, 3]: s += 3000
                        elif is_sapper: s += 400
                        elif my_r >= 8: s += 150

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
                if d_bm < old_d_bm: s += 45000

            # Doorway Clearance
            doorway = (2, 0) if enemy == 'red' else (9, 0)
            if fr == doorway and not is_sapper:
                if tc != 0: s += 50000
                else: s -= 50000

            # Flank breakthrough: push column 4 into enemy rear
            if fc == 4 and tc == 4 and my_r >= 7:
                if (p == 'red' and tr > fr) or (p == 'black' and tr < fr):
                    s += 120

            # General advance
            if p == 'red' and tr > fr: s += 60
            if p == 'black' and tr < fr: s += 60

        elif a['type'] == 'drop':
            tr, tc = a['to']
            c = a['card']
            # Tactical Drop Pressure: drop forward into frontline
            if (p == 'red' and tr == 4) or (p == 'black' and tr == 7):
                s += 600
            elif tc in [0, 4]:
                s += 400
            else:
                s += 150
        a['s'] = s

    acts.sort(key=lambda x: x['s'], reverse=True)
    return acts[0]

rgt.STRAT_REGISTRY['m5_grandmaster_v2'] = m5_grandmaster_v2

print("Testing m5_grandmaster_v2 vs m4_upgraded (50 RED, 50 BLK)...")
w_new, w_old, draws = 0, 0, 0
for _ in range(50):
    w, _ = rgt.play_match('m5_grandmaster_v2', 'm4_upgraded', tier1=1, tier2=1, max_turns=300)
    if w == 'red': w_new += 1
    elif w == 'black': w_old += 1
    else: draws += 1

for _ in range(50):
    w, _ = rgt.play_match('m4_upgraded', 'm5_grandmaster_v2', tier1=1, tier2=1, max_turns=300)
    if w == 'black': w_new += 1
    elif w == 'red': w_old += 1
    else: draws += 1

print(f"Result: M5_V2 Wins={w_new} | M4 Wins={w_old} | Draws={draws}")
dec = w_new + w_old
if dec > 0:
    print(f"Decisive Win Rate: {(w_new / dec * 100):.2f}%")
