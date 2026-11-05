import tournament_engine_core as tec
import test_v6_ambush as s6

g = tec.FastMatchEngine('v5_pincer', 'v6_ambush', red_tier=1, blk_tier=1)
for i in range(85):
    if g.game_state != 'playing': break
    act = tec.STRAT_REGISTRY[g.strats[g.current_turn]](g, g.current_turn)
    if not act: break
    c = act['card']; t = act['target']
    c_s = f"{c.rank}{c.suit}" if not c.is_flag else "FLAG"
    t_s = f" vs {t.rank}{t.suit}" if t else ""
    if i >= 35:
        print(f"T{i+1:2d} {g.current_turn.upper()}: {act['type']} {c_s} {act.get('from')}->{act['to']}{t_s}")
    g.execute(act)
print("FINAL WINNER:", g.winner, g.win_reason)
