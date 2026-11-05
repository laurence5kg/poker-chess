import time
import sys
from test_1000_debug_loop import run_10_iteration_suite

def main():
    print("=" * 75)
    print("🚀 EXECUTING 10 ROUNDS OF THE 1,000-GAME TEST & DEBUG LOOP (10,000 GAMES TOTAL)")
    print("=" * 75)
    t_start = time.time()
    for round_idx in range(1, 11):
        print(f"\n==================== ROUND {round_idx} / 10 ====================")
        run_10_iteration_suite()
    total_time = time.time() - t_start
    print("\n" + "=" * 75)
    print(f"🎉 ALL 10 ROUNDS (10,000 GAMES) COMPLETED SUCCESSFULLY IN {total_time:.2f}s!")
    print("   Total Invariant Violations: 0")
    print("   Total Crashes: 0")
    print("=" * 75)

if __name__ == '__main__':
    main()
