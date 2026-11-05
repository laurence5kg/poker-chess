import master_10_ladder as m10
import tune_remaining_3 as tr3

g = m10.FastMatchEngine('v8', 'v9_calib', red_tier=1, blk_tier=1)
for i in range(85):
    if g.game_state != 'playing': break
    act = m10.STRAT_REGISTRY[g.strats[g.current_turn]](g, g.current_turn)
    c = act['card']; t = act['target']
    c_s = f"{c.rank}{c.suit}" if not c.is_flag else "FLAG"
    t_s = f" vs {t.rank}{t.suit}" if t else ""
    if i >= 35:
        print(f"T{i+1:2d} {g.current_turn.upper()}: {act['type']} {c_s} {act.get('from')}->{act['to']}{t_s}")
    g.execute(act)
print("FINAL WINNER:", g.winner, g.win_reason)
