import run_grandmaster_tournaments as rgt

g = rgt.FastMatchEngine('m3_v3', 'm4_v4', red_tier=1, blk_tier=1)
print("=== TRACING RED=M3 vs BLACK=M4 ===")
for step in range(120):
    if g.game_state != 'playing': break
    p = g.current_turn
    s = g.strats[p]
    act = rgt.STRAT_REGISTRY[s](g, p)
    if not act: 
        print("No act for", p)
        break
    c = act['card']
    c_info = f"{c.rank}{c.suit}" if not c.is_flag else "FLAG"
    target = act['target']
    t_info = f" vs {target.rank}{target.suit}" if target else ""
    if step > 30:
        print(f"Turn {step+1:2d} {p.upper():5s} [{s}]: {act['type']} {c_info} from {act.get('from')} to {act['to']}{t_info}")
    g.execute(act)
print("WINNER:", g.winner, g.win_reason, "in", step+1, "turns")
