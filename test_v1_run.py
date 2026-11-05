import tournament_engine_core as tec
import random

# V0: Baseline Random Mover
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

# V1: Reserve Dropper + Memory Invariant (Strict Veto)
def v1(game, p):
    acts = game.get_actions(p)
    if not acts: return None
    enemy = 'black' if p == 'red' else 'red'
    flag_pos = (0, 0) if enemy == 'red' else (11, 0)
    my_flag = (0, 0) if p == 'red' else (11, 0)

    # 1. Mate in 1
    for a in acts:
        if a['type'] == 'move' and a['to'] == flag_pos: return a

    # 2. Immediate Starting Reserves Deployment
    for a in acts:
        if a['type'] == 'drop' and a['hand'] == 'starting':
            tr, tc = a['to']
            if (p == 'red' and tr == 4) or (p == 'black' and tr == 7):
                return a

    # 3. Flag Guard
    for r in range(12):
        for c in range(5):
            ec = game.board[r][c]
            if ec and ec.player == enemy and abs(r - my_flag[0]) + abs(c - my_flag[1]) <= 2:
                for a in acts:
                    if a['type'] == 'move' and a['to'] == (r, c) and (a['card'].rank_val > 0 or a['card'].is_bomb):
                        return a

    # 4. Standard Scoring with Strict Veto
    for a in acts:
        s = 15
        if a['type'] == 'move':
            fr, fc = a['from']
            tr, tc = a['to']
            c = a['card']
            tgt = a['target']
            is_sapper = c.is_sapper or c.is_mochigoma
            my_r = c.rank_val

            if tgt and tgt.player == enemy:
                k = game.memory[p].get(tgt.id)
                if k:
                    if k['is_flag']: return a
                    elif k['is_landmine']: s += (10000 if is_sapper else -500000)
                    elif k['rank_val'] > 0:
                        if c.is_bomb: s += 15000 + k['rank_val'] * 300
                        elif is_sapper: s = -9999999
                        elif my_r > k['rank_val']: s += 5000 + k['rank_val'] * 200
                        elif my_r == k['rank_val']: s += 30
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

tec.STRAT_REGISTRY['v0'] = v0
tec.STRAT_REGISTRY['v1'] = v1

w, l, d, rate, dt = tec.run_tournament_stage('v1', 'v0', 1, 0, 100)
print(f"STAGE 1 (V1 vs V0): W={w}, L={l}, D={d}, Decisive Rate={rate:.1f}% in {dt:.1f}s")
