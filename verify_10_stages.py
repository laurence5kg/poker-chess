import run_10_models_tournament as r10
import time

# Let's define the 10 evolutionary stages with carefully calibrated parameters

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

import random

# V1: Linear Heuristic + Memory Non-Suicide (tier 1 formation)
def v1(game, p):
    acts = game.get_actions(p)
    if not acts: return None
    enemy = 'black' if p == 'red' else 'red'
    flag_pos = (0, 0) if enemy == 'red' else (11, 0)
    for a in acts:
        s = 15
        if a['type'] == 'move':
            fr, fc = a['from']
            tr, tc = a['to']
            c = a['card']
            tgt = a['target']
            is_sapper = c.is_sapper or c.is_mochigoma
            if (tr, tc) == flag_pos: return a
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
                        else: s = -9999999 # Strict Veto
                elif (tr, tc) in game.known_mines[p]: s += (10000 if is_sapper else -500000)
                else: s += 40
            if p == 'red' and tr > fr: s += 30
            if p == 'black' and tr < fr: s += 30
            old_d = abs(fr - flag_pos[0]) + abs(fc - flag_pos[1])
            new_d = abs(tr - flag_pos[0]) + abs(tc - flag_pos[1])
            if new_d < old_d: s += 25
        elif a['type'] == 'drop': s += 20
        a['s'] = s
    acts.sort(key=lambda x: x['s'], reverse=True)
    return acts[0]

# V2: Threat Zone Evasion (Avoids stepping next to known larger enemy cards)
def v2(game, p):
    acts = game.get_actions(p)
    if not acts: return None
    enemy = 'black' if p == 'red' else 'red'
    flag_pos = (0, 0) if enemy == 'red' else (11, 0)
    for a in acts:
        s = 20
        if a['type'] == 'move':
            fr, fc = a['from']
            tr, tc = a['to']
            c = a['card']
            tgt = a['target']
            my_r = c.rank_val
            is_sapper = c.is_sapper or c.is_mochigoma
            if (tr, tc) == flag_pos: return a
            if tgt and tgt.player == enemy:
                k = game.memory[p].get(tgt.id)
                if k:
                    if k['is_flag']: return a
                    elif k['is_landmine']: s += (20000 if is_sapper else -500000)
                    elif k['rank_val'] > 0:
                        if c.is_bomb: s += 25000 + k['rank_val'] * 500
                        elif is_sapper: s = -9999999
                        elif my_r > k['rank_val']: s += 15000 + k['rank_val'] * 300
                        elif my_r == k['rank_val']: s += 50
                        else: s = -9999999
                elif (tr, tc) in game.known_mines[p]: s += (20000 if is_sapper else -500000)
                else: s += 40

            # Threat Zone Evasion
            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nr, nc = tr + dr, tc + dc
                if 0 <= nr < 12 and 0 <= nc < 5:
                    adj = game.board[nr][nc]
                    if adj and adj.player == enemy:
                        k_adj = game.memory[p].get(adj.id)
                        if k_adj and k_adj['rank_val'] > my_r:
                            s -= 80000 # Threat penalty

            if p == 'red' and tr > fr: s += 30
            if p == 'black' and tr < fr: s += 30
            old_d = abs(fr - flag_pos[0]) + abs(fc - flag_pos[1])
            new_d = abs(tr - flag_pos[0]) + abs(tc - flag_pos[1])
            if new_d < old_d: s += 35
        elif a['type'] == 'drop': s += 20
        a['s'] = s
    acts.sort(key=lambda x: x['s'], reverse=True)
    return acts[0]

# V3: Camp Defense Proximity
def v3(game, p):
    acts = game.get_actions(p)
    if not acts: return None
    enemy = 'black' if p == 'red' else 'red'
    flag_pos = (0, 0) if enemy == 'red' else (11, 0)
    my_camp = [0, 1, 2, 3, 4] if p == 'red' else [11, 10, 9, 8, 7]

    for a in acts:
        s = 25
        if a['type'] == 'move':
            fr, fc = a['from']
            tr, tc = a['to']
            c = a['card']
            tgt = a['target']
            my_r = c.rank_val
            is_sapper = c.is_sapper or c.is_mochigoma
            if (tr, tc) == flag_pos: return a

            # Camp Defense
            if tgt and tgt.player == enemy and tr in my_camp:
                if my_r > 0: s += 100000

            if tgt and tgt.player == enemy:
                k = game.memory[p].get(tgt.id)
                if k:
                    if k['is_flag']: return a
                    elif k['is_landmine']: s += (30000 if is_sapper else -500000)
                    elif k['rank_val'] > 0:
                        if c.is_bomb: s += 35000 + k['rank_val'] * 500
                        elif is_sapper: s = -9999999
                        elif my_r > k['rank_val']: s += 25000 + k['rank_val'] * 400
                        elif my_r == k['rank_val']: s += 50
                        else: s = -9999999
                elif (tr, tc) in game.known_mines[p]: s += (30000 if is_sapper else -500000)
                else: s += 50

            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nr, nc = tr + dr, tc + dc
                if 0 <= nr < 12 and 0 <= nc < 5:
                    adj = game.board[nr][nc]
                    if adj and adj.player == enemy:
                        k_adj = game.memory[p].get(adj.id)
                        if k_adj and k_adj['rank_val'] > my_r:
                            s -= 80000

            if p == 'red' and tr > fr: s += 35
            if p == 'black' and tr < fr: s += 35
            old_d = abs(fr - flag_pos[0]) + abs(fc - flag_pos[1])
            new_d = abs(tr - flag_pos[0]) + abs(tc - flag_pos[1])
            if new_d < old_d: s += 40
        elif a['type'] == 'drop': s += 20
        a['s'] = s
    acts.sort(key=lambda x: x['s'], reverse=True)
    return acts[0]

# Let's test v1 vs v0, v2 vs v1, v3 vs v2
r10.STRAT_REGISTRY['v0'] = v0
r10.STRAT_REGISTRY['v1'] = v1
r10.STRAT_REGISTRY['v2'] = v2
r10.STRAT_REGISTRY['v3'] = v3

print("--- TESTING EARLY STAGES ---")
w, l, d, rate, _ = r10.run_tournament_stage('v1', 'v0', 1, 0, 100)
print(f"v1 vs v0: {rate:.1f}% (W={w}, L={l}, D={d})")

w, l, d, rate, _ = r10.run_tournament_stage('v2', 'v1', 1, 1, 100)
print(f"v2 vs v1: {rate:.1f}% (W={w}, L={l}, D={d})")

w, l, d, rate, _ = r10.run_tournament_stage('v3', 'v2', 1, 1, 100)
print(f"v3 vs v2: {rate:.1f}% (W={w}, L={l}, D={d})")
