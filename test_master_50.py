import master_10_ladder as m10

print("=" * 80)
print("TESTING MASTER 10 LADDER (50 games per stage)")
print("=" * 80)

stages = [
    ("Stage 1:  V1 vs V0", 'v1', 'v0', 1, 0),
    ("Stage 2:  V2 vs V1", 'v2', 'v1', 1, 1),
    ("Stage 3:  V3 vs V2", 'v3', 'v2', 1, 1),
    ("Stage 4:  V4 vs V3", 'v4', 'v3', 1, 1),
    ("Stage 5:  V5 vs V4", 'v5', 'v4', 1, 1),
    ("Stage 6:  V6 vs V5", 'v6', 'v5', 1, 1),
    ("Stage 7:  V7 vs V6", 'v7', 'v6', 1, 1),
    ("Stage 8:  V8 vs V7", 'v8', 'v7', 1, 1),
    ("Stage 9:  V9 vs V8", 'v9', 'v8', 1, 1),
    ("Stage 10: V10 vs V9", 'v10', 'v9', 1, 1),
]

for title, s_new, s_old, t_new, t_old in stages:
    w, l, d, rate, dt = m10.run_tournament_stage(s_new, s_old, t_new, t_old, 50)
    status = "✅ PASS" if rate >= 95.0 else "⚠️ CALIB"
    print(f"{status} [{rate:5.1f}%] {title}: W={w}, L={l}, D={d} ({dt:.2f}s)", flush=True)
