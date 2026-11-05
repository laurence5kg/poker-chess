import run_10_models_tournament as r10

# Let's inspect stage 1: v1_memory_veto vs v0_baseline
print("Testing Stage 1 calibration...")
w1, w0, d, rate, dt = r10.run_tournament_stage('v1_memory_veto', 'v0_baseline', 1, 0, games=200)
print(f"Stage 1: Rate={rate:.2f}%, W1={w1}, W0={w0}, D={d}")
