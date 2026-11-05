import tournament_engine_core as tec

# Red naive pusher: pushes col 0
def red_rusher(game, p):
    acts = game.get_actions(p)
    if not acts: return None
    enemy = 'black' if p == 'red' else 'red'
    flag_pos = (0, 0) if enemy == 'red' else (11, 0)

    for a in acts:
        if a['type'] == 'move' and a['to'] == flag_pos: return a

    for a in acts:
        if a['type'] == 'drop' and a['hand'] == 'starting':
            tr, tc = a['to']
            if (p == 'red' and tr == 4) or (p == 'black' and tr == 7): return a

    for a in acts:
        s = 10
        if a['type'] == 'move':
            fr, fc = a['from']
            tr, tc = a['to']
            c = a['card']
            tgt = a['target']
            if tgt and tgt.player == enemy: s += 50000
            if fc == 0 and tc == 0: s += 500
            if p == 'red' and tr > fr: s += 50
            if p == 'black' and tr < fr: s += 50
        a['s'] = s
    acts.sort(key=lambda x: x['s'], reverse=True)
    return acts[0]

# Black ambusher: holds rank 7, lets enemy step into row 6, then strikes!
def black_ambusher(game, p):
    acts = game.get_actions(p)
    if not acts: return None
    enemy = 'black' if p == 'red' else 'red'
    flag_pos = (0, 0) if enemy == 'red' else (11, 0)

    for a in acts:
        if a['type'] == 'move' and a['to'] == flag_pos: return a

    for a in acts:
        if a['type'] == 'drop' and a['hand'] == 'starting':
            tr, tc = a['to']
            if (p == 'red' and tr == 4) or (p == 'black' and tr == 7): return a

    # If an enemy piece is adjacent, STRIKE IT!
    for a in acts:
        if a['type'] == 'move' and a['target'] and a['target'].player == enemy:
            return a

    # Otherwise, wait or reposition, DO NOT advance past row 6 (for Black) or row 5 (for Red)!
    for a in acts:
        s = 10
        if a['type'] == 'move':
            fr, fc = a['from']
            tr, tc = a['to']
            # Hold the defensive line
            if p == 'black' and tr < 7: s -= 1000 # Wait at row 7
            elif p == 'red' and tr > 4: s -= 1000 # Wait at row 4
            else: s += 50
        a['s'] = s
    acts.sort(key=lambda x: x['s'], reverse=True)
    return acts[0]

tec.STRAT_REGISTRY['rusher'] = red_rusher
tec.STRAT_REGISTRY['ambusher'] = black_ambusher

print("Match: Rusher (Red) vs Ambusher (Black)")
g = tec.FastMatchEngine('rusher', 'ambusher', 1, 1)
for i in range(25):
    if g.game_state != 'playing': break
    act = tec.STRAT_REGISTRY[g.strats[g.current_turn]](g, g.current_turn)
    c = act['card']; t = act['target']
    c_s = f"{c.rank}{c.suit}" if not c.is_flag else "FLAG"
    t_s = f" vs {t.rank}{t.suit}" if t else ""
    print(f"T{i+1:2d} {g.current_turn.upper()}: {act['type']} {c_s} {act.get('from')}->{act['to']}{t_s}")
    g.execute(act)
print("WINNER:", g.winner, g.win_reason)
