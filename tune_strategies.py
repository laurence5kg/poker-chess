import random
import time
import sys
from tournament_math_models import FastGameSim, STRATEGY_MAP, play_match, run_head_to_head

try:
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
except Exception:
    pass

def test_pair(v_new, v_old, n_games=200):
    print(f"\n--- Testing {v_new} vs {v_old} ({n_games} games) ---")
    w_new, w_old, draws, rate = run_head_to_head(v_new, v_old, games=n_games)
    print(f"Outcome: {v_new} Win Rate = {rate:.1f}%")
    return rate

if __name__ == '__main__':
    test_pair('v1', 'v0')
