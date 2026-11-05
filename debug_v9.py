import run_10_ladder_1000 as r

engine = r.FastMatchEngine(r.v8, r.v9, 1, 1)
for t in range(300):
    p = engine.current_turn
    strat = engine.strats[p]
    a = strat(engine, p)
    if not a:
        print(f"No actions for {p} on turn {t+1}")
        break
    engine.execute(a)
    if engine.game_state == 'ended':
        print(f"Game ended on turn {t+1}: winner={engine.winner}, reason={engine.win_reason}")
        break
else:
    print(f"Game reached 300 turns: state={engine.game_state}, winner={engine.winner}")
