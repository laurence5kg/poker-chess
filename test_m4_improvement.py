import run_grandmaster_tournaments as rgt
import random

def m4_upgraded(game, p):
    acts = game.get_actions(p)
    if not acts: return None
    enemy = 'black' if p == 'red' else 'red'
    flag_pos = (0, 0) if enemy == 'red' else (11, 0)
    my_flag = (0, 0) if p == 'red' else (11, 0)
    barrier_mine = (1, 0) if enemy == 'red' else (10, 0)
    bunker_rows = [0, 1] if enemy == 'red' else [10, 11]
    my_camp = [0, 1, 2, 3, 4] if p == 'red' else [11, 10, 9, 8, 7]
    enemy_camp = [11, 10, 9, 8, 7] if p == 'red' else [0, 1, 2, 3, 4]

    # 1. Win in 1
    for a in acts:
        if a['type'] == 'move':
            if a['to'] == flag_pos: return a
            if a['target'] and a['target'].player == enemy and a['target'].is_flag: return a

    # 2. Defcon 1: Kill any enemy piece inside our camp or near our flag
    for a in acts:
        if a['type'] == 'move':
            tr, tc = a['to']
            tgt = a['target']
            c = a['card']
            if tgt and tgt.player == enemy and tr in my_camp:
                # If we can kill it with an officer or bomb
                if c.rank_val > 0 or c.is_bomb:
                    # Check if safe capture
                    k = game.memory[p].get(id(tgt))
                    if not k or c.is_bomb or c.rank_val >= k.get('rank_val', 0):
                        return a

    # 3. Defensive Drop: Drop an officer right adjacent to an enemy intruder in our camp!
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
                        # Drop adjacent to intruder to block/intercept!
                        if a['card'].rank_val >= 7 or a['card'].is_bomb:
                            return a

    # 4. Find known enemy sapper / infiltrator
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

            # Priority 1: Intercept any intruder in our camp
            if intruders:
                for ir, ic, iec in intruders:
                    d = abs(tr - ir) + abs(tc - ic)
                    old_d = abs(fr - ir) + abs(fc - ic)
                    if d < old_d and (my_r >= 5 or c.is_bomb):
                        s += 150000

            # Priority 2: Hunt enemy sapper anywhere on board
            if enemy_sapper_pos and my_r >= 5:
                d_es = abs(tr - enemy_sapper_pos[0]) + abs(tc - enemy_sapper_pos[1])
                old_d_es = abs(fr - enemy_sapper_pos[0]) + abs(fc - enemy_sapper_pos[1])
                if d_es < old_d_es:
                    s += 80000

            # Combat evaluation
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
                        if my_r in [2, 3]: s += 2000 # Probe aggressively
                        elif is_sapper: s += 300
                        elif my_r >= 8: s += 100

            # Invincible 10 sweeper
            if my_r == 10 and ten_is_invincible:
                if tgt and tgt.player == enemy:
                    if tr in bunker_rows and tc in [0, 1, 2]: s -= 100000
                    else: s += 90000
                else:
                    d_flag = abs(tr - flag_pos[0]) + abs(tc - flag_pos[1])
                    s += (20 - d_flag) * 400

            # Sapper pathing to barrier mine
            if is_sapper:
                d_bm = abs(tr - barrier_mine[0]) + abs(tc - barrier_mine[1])
                old_d_bm = abs(fr - barrier_mine[0]) + abs(fc - barrier_mine[1])
                if d_bm < old_d_bm: s += 35000

            # Non-sapper step aside from doorway
            doorway = (2, 0) if enemy == 'red' else (9, 0)
            if fr == doorway and not is_sapper:
                if tc != 0: s += 40000
                else: s -= 40000

            # General advance
            if p == 'red' and tr > fr: s += 45
            if p == 'black' and tr < fr: s += 45

        elif a['type'] == 'drop':
            tr, tc = a['to']
            c = a['card']
            if intruders:
                # Handled above
                s += 10
            else:
                # Drop near front line or flanks
                if p == 'red' and tr == 4: s += 200
                elif p == 'black' and tr == 7: s += 200
                else: s += 20
        a['s'] = s

    acts.sort(key=lambda x: x['s'], reverse=True)
    return acts[0]

rgt.STRAT_REGISTRY['m4_upgraded'] = m4_upgraded

print("Testing m4_upgraded vs m3_v3 (50 games as RED, 50 games as BLK)...")
w_new, w_old, draws = 0, 0, 0
for _ in range(50):
    w, _ = rgt.play_match('m4_upgraded', 'm3_v3', tier1=1, tier2=1, max_turns=300)
    if w == 'red': w_new += 1
    elif w == 'black': w_old += 1
    else: draws += 1

for _ in range(50):
    w, _ = rgt.play_match('m3_v3', 'm4_upgraded', tier1=1, tier2=1, max_turns=300)
    if w == 'black': w_new += 1
    elif w == 'red': w_old += 1
    else: draws += 1

print(f"Result: M4_UPGRADED Wins={w_new} | M3_V3 Wins={w_old} | Draws={draws}")
print(f"Win Rate: {(w_new / (w_new + w_old) * 100):.2f}%")
