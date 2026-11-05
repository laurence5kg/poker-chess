import run_10_models_tournament as r10

stages = [
    ("STAGE 1: M1 (Memory Veto V1) vs Baseline (V0)", 'v1_memory_veto', 'v0_baseline', 1, 0),
    ("STAGE 2: M2 (Threat Zone V2) vs M1 (Memory Veto V1)", 'v2_threat_zone', 'v1_memory_veto', 1, 1),
    ("STAGE 3: M3 (Sapper Preserve V3) vs M2 (Threat Zone V2)", 'v3_sapper_preserve', 'v2_threat_zone', 1, 1),
    ("STAGE 4: M4 (Doorway Clear V4) vs M3 (Sapper Preserve V3)", 'v4_doorway_clear', 'v3_sapper_preserve', 1, 1),
    ("STAGE 5: M5 (Defcon 1 Homeland V5) vs M4 (Doorway Clear V4)", 'v5_homeland_defcon1', 'v4_doorway_clear', 1, 1),
    ("STAGE 6: M6 (Drop Blockade V6) vs M5 (Defcon 1 Homeland V5)", 'v6_drop_blockade', 'v5_homeland_defcon1', 1, 1),
    ("STAGE 7: M7 (Hunter-Killer V7) vs M6 (Drop Blockade V6)", 'v7_hunter_killer', 'v6_drop_blockade', 1, 1),
    ("STAGE 8: M8 (Invincible Sweep V8) vs M7 (Hunter-Killer V7)", 'v8_invincible_sweep', 'v7_hunter_killer', 1, 1),
    ("STAGE 9: M9 (Flank Pincer V9) vs M8 (Invincible Sweep V8)", 'v9_flank_pincer', 'v8_invincible_sweep', 1, 1),
    ("STAGE 10: M10 (Grandmaster Oracle V10) vs M9 (Flank Pincer V9)", 'v10_grandmaster_oracle', 'v9_flank_pincer', 1, 1),
]

for title, s_new, s_old, t_new, t_old in stages:
    w_new, w_old, draws, rate, dt = r10.run_tournament_stage(s_new, s_old, t_new, t_old, games=50)
    status = "✅ PASS" if rate >= 95.0 else "⚠️ CALIB"
    print(f"{status} [{rate:5.1f}%] {title}: {s_new} W={w_new} | {s_old} W={w_old} | D={draws} ({dt:.2f}s)", flush=True)
