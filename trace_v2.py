import run_grandmaster_tournaments as rgt
import tune_v2

print("=== GAME 1: V2_TUNED (Red) vs V1_MASTER (Black) ===")
g = rgt.FastMatchEngine('v2_tuned', 'v1_master', red_tier=1, blk_tier=1)
for step in range(40):
    if g.game_state != 'playing': break
    p = g.current_turn
    s = g.strats[p]
    act = rgt.STRAT_REGISTRY[s](g, p)
    if not act: break
    c = act['card']
    c_info = f"{c.rank}{c.suit}" if not c.is_flag else "FLAG"
    target = act['target']
    t_info = f" vs {target.rank}{target.suit}" if target else ""
    print(f"T{step+1:2d} {p.upper()} [{s}]: {act['type']} {c_info} from {act.get('from')} to {act['to']}{t_info}")
    g.execute(act)
print("WINNER:", g.winner, g.win_reason)

print("\n=== GAME 2: V1_MASTER (Red) vs V2_TUNED (Black) ===")
g2 = rgt.FastMatchEngine('v1_master', 'v2_tuned', red_tier=1, blk_tier=1)
for step in range(40):
    if g2.game_state != 'playing': break
    p = g2.current_turn
    s = g2.strats[p]
    act = rgt.STRAT_REGISTRY[s](g2, p)
    if not act: break
    c = act['card']
    c_info = f"{c.rank}{c.suit}" if not c.is_flag else "FLAG"
    target = act['target']
    t_info = f" vs {target.rank}{target.suit}" if target else ""
    print(f"T{step+1:2d} {p.upper()} [{s}]: {act['type']} {c_info} from {act.get('from')} to {act['to']}{t_info}")
    g2.execute(act)
print("WINNER:", g2.winner, g2.win_reason)
