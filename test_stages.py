import run_grandmaster_tournaments as rgt

g = rgt.FastMatchEngine('m3_v3', 'm4_v4', red_tier=1, blk_tier=1)
turns = 0
history = []
while g.game_state == 'playing' and turns < 300:
    p = g.current_turn
    s = g.strats[p]
    act = rgt.STRAT_REGISTRY[s](g, p)
    if not act: break
    c = act['card']
    c_info = f"{c.rank}{c.suit}" if not c.is_flag else "FLAG"
    target = act['target']
    t_info = f" vs {target.rank}{target.suit}" if target else ""
    history.append(f"Turn {turns+1:3d} {p.upper():5s} [{s}]: {act['type']} {c_info} from {act.get('from')} to {act['to']}{t_info}")
    g.execute(act)
    turns += 1

print("\n".join(history[-25:]))
