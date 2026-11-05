import run_grandmaster_tournaments as rgt
from tune_v1 import v1_master

def v2_tuned(game, p):
    acts = game.get_actions(p)
    if not acts: return None
    enemy = 'black' if p == 'red' else 'red'
    flag_pos = (0, 0) if enemy == 'red' else (11, 0)
    my_flag = (0, 0) if p == 'red' else (11, 0)
    my_camp = [0, 1, 2, 3, 4] if p == 'red' else [11, 10, 9, 8, 7]
    barrier_mine = (1, 0) if enemy == 'red' else (10, 0)

    # 1. Mate in 1
    for a in acts:
        if a['type'] == 'move' and a['to'] == flag_pos: return a

    # 2. Defend Flag if enemy within distance 3
    for r in range(12):
        for c in range(5):
            ec = game.board[r][c]
            if ec and ec.player == enemy and abs(r - my_flag[0]) + abs(c - my_flag[1]) <= 3:
                for a in acts:
                    if a['type'] == 'move' and a['to'] == (r, c):
                        if a['card'].rank_val > 0 or a['card'].is_bomb:
                            return a

    # 3. Intercept camp intruders
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
                    k = game.memory[p].get(id(tgt))
                    if c.is_bomb or (k and c.rank_val >= k['rank_val']) or (not k and c.rank_val >= 7):
                        return a

    # 4. Drop reserves immediately
    for a in acts:
        if a['type'] == 'drop':
            tr, tc = a['to']
            if (p == 'red' and tr == 4) or (p == 'black' and tr == 7):
                return a

    for a in acts:
        s = 20
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
                        s += 150000

            if tgt and tgt.player == enemy:
                cid = id(tgt)
                k = game.memory[p].get(cid)
                if k:
                    if k['is_flag']: return a
                    elif k['is_landmine']: s += (40000 if is_sapper else -500000)
                    elif k['rank_val'] > 0:
                        if c.is_bomb: s += 50000 + k['rank_val'] * 500
                        elif is_sapper: s = -9999999
                        elif my_r > k['rank_val']: s += 30000 + k['rank_val'] * 300
                        elif my_r == k['rank_val']: s += 30
                        else: s = -9999999
                elif (tr, tc) in game.known_mines[p]: s += (40000 if is_sapper else -500000)
                else: s += 60

            # Threat Zone Avoidance
            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nr, nc = tr + dr, tc + dc
                if 0 <= nr < 12 and 0 <= nc < 5:
                    adj = game.board[nr][nc]
                    if adj and adj.player == enemy:
                        k_adj = game.memory[p].get(id(adj))
                        if k_adj and k_adj.get('rank_val', 0) > my_r:
                            s -= 80000

            old_d = abs(fr - flag_pos[0]) + abs(fc - flag_pos[1])
            new_d = abs(tr - flag_pos[0]) + abs(tc - flag_pos[1])
            if new_d < old_d: s += 50

            if is_sapper and new_d < old_d: s += 4000

            if p == 'red' and tr > fr: s += 40
            if p == 'black' and tr < fr: s += 40
        elif a['type'] == 'drop': s += 20
        a['s'] = s
    acts.sort(key=lambda x: x['s'], reverse=True)
    return acts[0]

rgt.STRAT_REGISTRY['v2_tuned'] = v2_tuned

w, l, d, rate, dt = rgt.run_tournament_stage('v2_tuned', 'v1_master', 1, 1, 100)
print(f"V2_TUNED vs V1_MASTER: Win Rate = {rate:.2f}% (W={w}, L={l}, D={d}) in {dt:.1f}s")
