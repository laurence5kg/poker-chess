import run_10_ladder_1000 as r

g = r.FastMatchEngine('v9', 'v8', 1, 1)
turns = 0
while g.game_state == 'playing' and turns < 300:
    p = g.current_turn
    strat = r.STRAT_REGISTRY[g.strats[p]]
    act = strat(g, p)
    if not act:
        print(f"Turn {turns+1}: {p} returned no action!")
        break
    g.execute(act)
    turns += 1
    if turns >= 145:
        if act['type'] == 'move':
            print(f"Turn {turns:03d} [{p}]: {act['card'].rank} from {act['from']} to {act['to']} (tgt={act['target']})")
        else:
            print(f"Turn {turns:03d} [{p}]: drop {act['card'].rank} to {act['to']}")

print(f"Game State: {g.game_state}, Winner: {g.winner}, Win Reason: {g.win_reason}")
