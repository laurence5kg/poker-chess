import tournament_engine_core as tec
import test_v6_ambush as s6

g = tec.FastMatchEngine('v5_pincer', 'v6_ambush', red_tier=1, blk_tier=1)
for i in range(35):
    if g.game_state != 'playing': break
    act = tec.STRAT_REGISTRY[g.strats[g.current_turn]](g, g.current_turn)
    c = act['card']; t = act['target']
    c_s = f"{c.rank}{c.suit}" if not c.is_flag else "FLAG"
    t_s = f" vs {t.rank}{t.suit}" if t else ""
    print(f"T{i+1:2d} {g.current_turn.upper()}: {act['type']} {c_s} {act.get('from')}->{act['to']}{t_s}")
    g.execute(act)
print("WINNER:", g.winner, g.win_reason)
