import random
import time
import sys
from test_v2 import FastSim, v1_memory

def v2_with_defense(game, p):
    acts = game.get_actions(p)
    if not acts: return None
    enemy = 'black' if p == 'red' else 'red'
    flag_pos = (0, 0) if enemy == 'red' else (11, 0)
    my_flag = (0, 0) if p == 'red' else (11, 0)
    bunker_rows = [0, 1] if enemy == 'red' else [10, 11]
    my_camp_rows = [0, 1, 2, 3, 4] if p == 'red' else [11, 10, 9, 8, 7]

    # 1. Win in 1: Flag Snipe
    for a in acts:
        if a['type'] == 'move':
            if a['to'] == flag_pos: return a
            if a['target'] and a['target'].player == enemy and a['target'].is_flag: return a

    for a in acts:
        s = 20
        if a['type'] == 'move':
            fr, fc = a['from']
            tr, tc = a['to']
            c = a['card']
            tgt = a['target']
            my_r = c.rank_val
            is_sapper = c.is_sapper or c.is_mochigoma

            # 2. EMERGENCY HOMELAND DEFENSE: Intercept ANY enemy intruder in our camp!
            if tgt and tgt.player == enemy and tr in my_camp_rows:
                if my_r > 0: # An officer attacking the intruder
                    s += 80000 # Intercept intruder with absolute priority!
                    if tgt.is_sapper or tgt.is_mochigoma:
                        s += 40000 # Extra priority to assassinate enemy sappers!

            # 3. Guarding the approach to our Flag:
            d_to_my_flag = abs(tr - my_flag[0]) + abs(tc - my_flag[1])
            for r in my_camp_rows:
                for col in range(5):
                    ec = game.board[r][col]
                    if ec and ec.player == enemy:
                        # Intruder detected!
                        d_intruder = abs(tr - r) + abs(tc - col)
                        old_d_intruder = abs(fr - r) + abs(fc - col)
                        if d_intruder < old_d_intruder and my_r > 0:
                            s += 35000 # Rush to intercept intruder!

            if tgt and tgt.player == enemy:
                cid = id(tgt)
                k = game.memory[p].get(cid)
                if k:
                    if k['is_flag']: return a
                    elif k['is_landmine']:
                        s += 50000 if is_sapper else -100000
                    elif k['rank_val'] > 0:
                        if c.is_bomb:
                            s += 60000 + k['rank_val'] * 1000
                        elif is_sapper:
                            s -= 50000
                        elif my_r > k['rank_val']:
                            s += 20000 + k['rank_val'] * 500
                        elif my_r == k['rank_val']:
                            s += 10
                        else:
                            s -= 50000
                elif (tr, tc) in game.known_mines[p]:
                    s += 50000 if is_sapper else -100000
                else:
                    if tr in bunker_rows and tc in [0, 1, 2]:
                        if is_sapper: s += 40000
                        else: s -= 100000
                    else:
                        if my_r in [2, 3]: s += 800
                        elif is_sapper: s -= 2000
                        elif my_r >= 8: s += 50

            # Sapper pathing to enemy flag
            if is_sapper:
                d_flag = abs(tr - flag_pos[0]) + abs(tc - flag_pos[1])
                old_d_flag = abs(fr - flag_pos[0]) + abs(fc - flag_pos[1])
                if d_flag < old_d_flag: s += 1500

            # Forward bias
            if p == 'red' and tr > fr: s += 25
            if p == 'black' and tr < fr: s += 25

        elif a['type'] == 'drop':
            # Intercept drop: Drop directly in front of intruder
            tr, tc = a['to']
            for r in my_camp_rows:
                for col in range(5):
                    ec = game.board[r][col]
                    if ec and ec.player == enemy:
                        d = abs(tr - r) + abs(tc - col)
                        if d <= 1: s += 50000
            s += 25
        a['s'] = s

    acts.sort(key=lambda x: x['s'], reverse=True)
    return acts[0]

def test():
    w_new, w_old, draws = 0, 0, 0
    games = 200
    for i in range(games // 2):
        g = FastSim('v2', 'v1', red_form='counter_trap', blk_form='random')
        turns = 0
        while g.game_state == 'playing' and turns < 300:
            act = v2_with_defense(g, 'red') if g.current_turn == 'red' else v1_memory(g, 'black')
            if not act: break
            g.execute(act)
            turns += 1
        if g.winner == 'red': w_new += 1
        elif g.winner == 'black': w_old += 1
        else: draws += 1

    for i in range(games // 2):
        g = FastSim('v1', 'v2', red_form='random', blk_form='counter_trap')
        turns = 0
        while g.game_state == 'playing' and turns < 300:
            act = v1_memory(g, 'red') if g.current_turn == 'red' else v2_with_defense(g, 'black')
            if not act: break
            g.execute(act)
            turns += 1
        if g.winner == 'black': w_new += 1
        elif g.winner == 'red': w_old += 1
        else: draws += 1

    dec = w_new + w_old
    rate = w_new / dec * 100 if dec > 0 else 0
    print(f"V2 Wins: {w_new} | V1 Wins: {w_old} | Draws: {draws} | Decisive Win Rate: {rate:.2f}%")

if __name__ == '__main__':
    test()
