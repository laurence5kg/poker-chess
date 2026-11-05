import re

with open('app.js', encoding='utf-8') as f:
    text = f.read()

print("=== APP.JS PVE MATCHES ===")
for m in re.finditer(r'pve', text, re.IGNORECASE):
    s = max(0, m.start() - 60)
    e = min(len(text), m.end() + 100)
    print(text[s:e].replace('\n', ' '))
    print('---')

with open('game.js', encoding='utf-8') as f:
    text_g = f.read()

print("=== GAME.JS PVE MATCHES ===")
for m in re.finditer(r'pve', text_g, re.IGNORECASE):
    s = max(0, m.start() - 60)
    e = min(len(text_g), m.end() + 100)
    print(text_g[s:e].replace('\n', ' '))
    print('---')
