import run_grandmaster_tournaments as rgt
import run_10_models_tournament as r10

# Register rgt strats in r10
for k, v in rgt.STRAT_REGISTRY.items():
    r10.STRAT_REGISTRY[k] = v

print("--- TESTING PROVEN PAIRS FROM RUN_GRANDMASTER_TOURNAMENTS ---")
w, l, d, rate, dt = r10.run_tournament_stage('m2_v2', 'm1_v1', 1, 1, 100)
print(f"m2_v2 vs m1_v1: {rate:.1f}% (W={w}, L={l}, D={d}) in {dt:.1f}s")

w, l, d, rate, dt = r10.run_tournament_stage('m3_v3', 'm2_v2', 1, 1, 100)
print(f"m3_v3 vs m2_v2: {rate:.1f}% (W={w}, L={l}, D={d}) in {dt:.1f}s")

w, l, d, rate, dt = r10.run_tournament_stage('m4_v4', 'm3_v3', 1, 1, 100)
print(f"m4_v4 vs m3_v3: {rate:.1f}% (W={w}, L={l}, D={d}) in {dt:.1f}s")

w, l, d, rate, dt = r10.run_tournament_stage('m5_v5', 'm4_v4', 1, 1, 100)
print(f"m5_v5 vs m4_v4: {rate:.1f}% (W={w}, L={l}, D={d}) in {dt:.1f}s")
