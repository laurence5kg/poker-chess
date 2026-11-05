import run_grandmaster_tournaments as rgt
import tune_v2

g = rgt.FastMatchEngine('v2_tuned', 'v1_master', red_tier=1, blk_tier=1)
for i in range(115):
    if g.game_state != 'playing': break
    act = rgt.STRAT_REGISTRY[g.strats[g.current_turn]](g, g.current_turn)
    if not act: break
    c = act['card']
    t = act['target']
    c_str = f"{c.rank}{c.suit}" if not c.is_flag else "FLAG"
    t_str = f" vs {t.rank}{t.suit}" if t else ""
    if i >= 85:
        print(f"T{i+1:3d} {g.current_turn.upper()}: {act['type']} {c_str} {act.get('from')}->{act['to']}{t_str}")
    g.execute(act)
print("WINNER:", g.winner, g.win_reason)
