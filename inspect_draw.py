import run_grandmaster_tournaments as rgt
from test_m4_improvement import m4_upgraded
from test_m5_vs_m4 import m5_grandmaster_v2

rgt.STRAT_REGISTRY['m4_upgraded'] = m4_upgraded
rgt.STRAT_REGISTRY['m5_grandmaster_v2'] = m5_grandmaster_v2

g = rgt.FastMatchEngine('m4_upgraded', 'm5_grandmaster_v2', red_tier=1, blk_tier=1)
turns = 0
while g.game_state == 'playing' and turns < 300:
    p = g.current_turn
    s = g.strats[p]
    act = rgt.STRAT_REGISTRY[s](g, p)
    if not act: break
    g.execute(act)
    turns += 1

print(f"Result: {g.winner}, Reason: {g.win_reason}, Turns: {turns}")
print("Final board:")
for r in range(12):
    row_str = []
    for c in range(5):
        card = g.board[r][c]
        if not card: row_str.append(" . ")
        else:
            rank = card.rank[0] if len(card.rank) > 1 else card.rank
            side = 'R' if card.player == 'red' else 'B'
            row_str.append(f"{side}{rank}{card.suit}")
    print(f"Row {r:2d}: {' '.join(row_str)}")
print("M4 Red Hand:", [c.rank for c in g.hands['red']['starting'] + g.hands['red']['mochigoma']])
print("M5 Black Hand:", [c.rank for c in g.hands['black']['starting'] + g.hands['black']['mochigoma']])
