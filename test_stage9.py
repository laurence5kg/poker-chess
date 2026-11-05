import run_10_ladder_1000 as r

w1, t1 = r.play_match('v9', 'v8', 1, 1)
print(f"Match 1 (Red=v9, Black=v8): Winner={w1}, turns={t1}")

w2, t2 = r.play_match('v8', 'v9', 1, 1)
print(f"Match 2 (Red=v8, Black=v9): Winner={w2}, turns={t2}")
