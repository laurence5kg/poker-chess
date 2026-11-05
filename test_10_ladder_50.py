import run_10_ladder_full as rlf

print("Testing run_10_ladder_full with 50 games per stage...")
stages = [
    ("STAGE 1:  M1 vs Baseline (V0)", 'v1', 'v0', 1, 0),
    ("STAGE 2:  M2 vs M1 (V1)", 'v2', 'v1', 1, 1),
    ("STAGE 3:  M3 vs M2 (V2)", 'v3', 'v2', 1, 1),
    ("STAGE 4:  M4 vs M3 (V3)", 'v4', 'v3', 1, 1),
    ("STAGE 5:  M5 vs M4 (V4)", 'v5', 'v4', 1, 1),
    ("STAGE 6:  M6 vs M5 (V5)", 'v6', 'v5', 1, 1),
    ("STAGE 7:  M7 vs M6 (V6)", 'v7', 'v6', 1, 1),
    ("STAGE 8:  M8 vs M7 (V7)", 'v8', 'v7', 1, 1),
    ("STAGE 9:  M9 vs M8 (V8)", 'v9', 'v8', 1, 1),
    ("STAGE 10: M10 vs M9 (V9)", 'v10', 'v9', 1, 1),
]

for title, s_new, s_old, t_new, t_old in stages:
    w, l, d, rate, dt = rlf.run_tournament_stage(s_new, s_old, t_new, t_old, 50)
    status = "✅ PASS" if rate >= 95.0 else "⚠️ CALIB"
    print(f"{status} [{rate:5.1f}%] {title}: W={w}, L={l}, D={d} ({dt:.2f}s)", flush=True)
