import tournament_engine_core as tec
import test_v3_run as s3

g = tec.FastMatchEngine('v3', 'v2', red_tier=1, blk_tier=1)
for i in range(50):
    if g.game_state != 'playing': break
    act = tec.STRAT_REGISTRY[g.strats[g.current_turn]](g, g.current_turn)
    if not act: break
    c = act['card']
    t = act['target']
    c_str = f"{c.rank}{c.suit}" if not c.is_flag else "FLAG"
    t_str = f" vs {t.rank}{t.suit}" if t else ""
    print(f"T{i+1:2d} {g.current_turn.upper()} [{g.strats[g.current_turn]}]: {act['type']} {c_str} {act.get('from')}->{act['to']}{t_str}")
    g.execute(act)
print("WINNER:", g.winner, g.win_reason)
