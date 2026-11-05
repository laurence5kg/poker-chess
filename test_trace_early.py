import run_10_ladder_1000 as r

g = r.FastMatchEngine('v9', 'v8', 1, 1)
turns = 0
while g.game_state == 'playing' and turns < 100:
    p = g.current_turn
    strat = r.STRAT_REGISTRY[g.strats[p]]
    act = strat(g, p)
    if not act: break
    g.execute(act)
    turns += 1
    if act['type'] == 'move':
        tgt_str = f"x {act['target'].rank} ({act['target'].player})" if act['target'] else ""
        print(f"T{turns:02d} [{p:5s}]: {act['card'].rank} from {act['from']} to {act['to']} {tgt_str}")
    else:
        print(f"T{turns:02d} [{p:5s}]: drop {act['card'].rank} to {act['to']}")

print("Graveyard:")
print("Red:", [c.rank for c in g.graveyard if c.player == 'red'])
print("Black:", [c.rank for c in g.graveyard if c.player == 'black'])
print("Red Hand (Mochigoma):", [c.rank for c in g.hands['red']['mochigoma']])
print("Black Hand (Mochigoma):", [c.rank for c in g.hands['black']['mochigoma']])
