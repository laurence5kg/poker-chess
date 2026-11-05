import random
import time
import sys
from comprehensive_math_models_test import FastSim, Card, v1_memory, OFFICER_RANKS

def v2_probe_ambush(game, p):
    acts = game.get_actions(p)
    if not acts: return None
    enemy = 'black' if p == 'red' else 'red'
    flag_pos = (0, 0) if enemy == 'red' else (11, 0)
    bunker_rows = [0, 1] if enemy == 'red' else [10, 11]

    # 1. Immediate Flag Capture (Win in 1)
    for a in acts:
        if a['type'] == 'move':
            if a['to'] == flag_pos: return a
            if a['target'] and a['target'].player == enemy and a['target'].is_flag: return a

    # Count enemy threats
    enemy_10s_dead = sum(1 for c in game.graveyard if c.rank == '10' and c.player == enemy)
    enemy_bombs_dead = sum(1 for c in game.graveyard if c.is_bomb and c.player == enemy)

    for a in acts:
        s = 20
        if a['type'] == 'move':
            fr, fc = a['from']
            tr, tc = a['to']
            c = a['card']
            tgt = a['target']
            my_r = c.rank_val
            is_sapper = c.is_sapper or c.is_mochigoma

            if tgt and tgt.player == enemy:
                cid = id(tgt)
                k = game.memory[p].get(cid)
                if k:
                    if k['is_flag']: return a
                    elif k['is_landmine']:
                        s += 50000 if is_sapper else -100000
                    elif k['rank_val'] > 0:
                        if c.is_bomb:
                            s += 60000 + k['rank_val'] * 1000 # Bomb assassinates revealed officer!
                        elif is_sapper:
                            s -= 50000
                        elif my_r > k['rank_val']:
                            s += 15000 + k['rank_val'] * 500
                        elif my_r == k['rank_val']:
                            s += 10
                        else:
                            s -= 50000
                elif (tr, tc) in game.known_mines[p]:
                    s += 50000 if is_sapper else -100000
                else:
                    # Target is UNREVEALED!
                    if tr in bunker_rows and tc in [0, 1, 2]:
                        # Inside enemy bunker: only sappers!
                        if is_sapper: s += 40000
                        else: s -= 100000
                    else:
                        if my_r in [2, 3]:
                            s += 800 # Low probes aggressively attack to reveal enemy cards!
                        elif is_sapper:
                            s -= 2000 # Don't risk sappers on unknown cards
                        elif my_r >= 8:
                            s -= 5000 # High officers NEVER attack unknown cards! Wait until revealed!

            # If our card is a Bomb, seek known enemy high officers!
            if c.is_bomb:
                for r in range(12):
                    for col in range(5):
                        ec = game.board[r][col]
                        if ec and ec.player == enemy:
                            ek = game.memory[p].get(id(ec))
                            if ek and ek['rank_val'] >= 8:
                                d = abs(tr - r) + abs(tc - col)
                                old_d = abs(fr - r) + abs(fc - col)
                                if d < old_d: s += 3000

            # Sapper pathing to enemy flag once enemy 10s are dead
            if is_sapper:
                d_flag = abs(tr - flag_pos[0]) + abs(tc - flag_pos[1])
                old_d_flag = abs(fr - flag_pos[0]) + abs(fc - flag_pos[1])
                if d_flag < old_d_flag: s += 1200

            # Forward bias
            if p == 'red' and tr > fr: s += 30
            if p == 'black' and tr < fr: s += 30

        elif a['type'] == 'drop':
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
            act = v2_probe_ambush(g, 'red') if g.current_turn == 'red' else v1_memory(g, 'black')
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
            act = v1_memory(g, 'red') if g.current_turn == 'red' else v2_probe_ambush(g, 'black')
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
