import run_grandmaster_tournaments as rgt
import tune_v2

g = rgt.FastMatchEngine('v2_tuned', 'v1_master', red_tier=1, blk_tier=1)
for i in range(104):
    if g.game_state != 'playing': break
    act = rgt.STRAT_REGISTRY[g.strats[g.current_turn]](g, g.current_turn)
    if not act: break
    c = act['card']
    t = act['target']
    c_str = f"{c.rank}{c.suit}" if not c.is_flag else "FLAG"
    t_str = f" vs {t.rank}{t.suit}" if t else ""
    if i in [94, 95, 96, 97, 98, 99, 100, 101, 102]:
        print(f"\n--- Turn {i+1} {g.current_turn.upper()} ---")
        for r in range(5):
            row_str = " ".join([f"{g.board[r][c].rank}{g.board[r][c].suit}({g.board[r][c].player[0]})" if g.board[r][c] else "  .  " for c in range(5)])
            print(f"R{r}: {row_str}")
        print(f"Action: {act['type']} {c_str} {act.get('from')}->{act['to']}{t_str}")
        acts = game_acts = g.get_actions(g.current_turn)
        moves_into_col0 = [a for a in acts if a['type'] == 'move' and a['to'][1] == 0]
        print(f"Legal moves to Col 0: {len(moves_into_col0)}")
    g.execute(act)
