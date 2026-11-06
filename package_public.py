import os, shutil

root_dir = r'C:\Users\27073\.gemini\antigravity\scratch\poker-shogi-junqi'
pub_dir = os.path.join(root_dir, 'public')
os.makedirs(pub_dir, exist_ok=True)

# 1. Copy runtime files: app.js, game.js, network.js, i18n.js, audio.js, style.css
for fname in ['app.js', 'game.js', 'network.js', 'i18n.js', 'audio.js', 'style.css']:
    src = os.path.join(root_dir, fname)
    dst = os.path.join(pub_dir, fname)
    shutil.copy2(src, dst)
    print(f"Copied {fname} -> public/{fname}")

# 2. Build public/index.html with version query strings and meta tags
with open(os.path.join(root_dir, 'index.html'), 'r', encoding='utf-8') as f:
    html = f.read()

# Update cache busting query strings to ?v=1.0.0
html = html.replace('href="style.css?v=4"', 'href="style.css?v=1.0.0"')
html = html.replace('src="i18n.js?v=4"', 'src="i18n.js?v=1.0.0"')
html = html.replace('src="audio.js?v=4"', 'src="audio.js?v=1.0.0"')
html = html.replace('src="game.js?v=4"', 'src="game.js?v=1.0.0"')
html = html.replace('src="app.js?v=4"', 'src="app.js?v=1.0.0"')

# Add Open Graph & Twitter meta tags in <head>
og_tags = '''    <link rel="canonical" href="./">
    <meta property="og:type" content="website">
    <meta property="og:title" content="Poker Chess (扑克军棋)">
    <meta property="og:description" content="A tactical turn-based strategy game combining Military Chess (Junqi), Shogi Mochigoma drops, and Poker hierarchy under Fog-of-War.">
    <meta property="og:image" content="favicon.svg">
    <meta name="twitter:card" content="summary">
    <meta name="twitter:title" content="Poker Chess (扑克军棋)">
    <meta name="twitter:description" content="A tactical turn-based strategy game combining Military Chess (Junqi), Shogi Mochigoma drops, and Poker hierarchy under Fog-of-War.">
    <link rel="icon" type="image/svg+xml" href="favicon.svg">
    <link rel="alternate icon" href="favicon.ico">'''

if '<meta property="og:type"' not in html:
    html = html.replace('    <link rel="stylesheet" href="style.css?v=1.0.0">', og_tags + '\n    <link rel="stylesheet" href="style.css?v=1.0.0">')

with open(os.path.join(pub_dir, 'index.html'), 'w', encoding='utf-8') as f:
    f.write(html)
print("Created public/index.html with cache busting & social meta tags")

# Also update root index.html to match cache busting
with open(os.path.join(root_dir, 'index.html'), 'w', encoding='utf-8') as f:
    f.write(html)
print("Synchronized root index.html")

# 3. Create public/favicon.svg
svg_content = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
  <rect width="100" height="100" rx="20" fill="#113322" stroke="#d4af37" stroke-width="4"/>
  <text x="50" y="68" font-size="54" text-anchor="middle" fill="#d4af37" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif" font-weight="bold">🃏</text>
</svg>'''
with open(os.path.join(pub_dir, 'favicon.svg'), 'w', encoding='utf-8') as f:
    f.write(svg_content)
with open(os.path.join(root_dir, 'favicon.svg'), 'w', encoding='utf-8') as f:
    f.write(svg_content)
print("Created favicon.svg")

# 4. Create public/favicon.ico (minimal standard 16x16 ICO header or symlink)
# We can create a valid 16x16 single-color/icon ICO binary
ico_bytes = bytes([
    0x00, 0x00, 0x01, 0x00, 0x01, 0x00, 0x10, 0x10, 0x00, 0x00, 0x01, 0x00, 0x20, 0x00, 0x68, 0x04,
    0x00, 0x00, 0x16, 0x00, 0x00, 0x00, 0x28, 0x00, 0x00, 0x00, 0x10, 0x00, 0x00, 0x00, 0x20, 0x00,
    0x00, 0x00, 0x01, 0x00, 0x20, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x04, 0x00, 0x00, 0x00, 0x00,
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00
] + [0x11, 0x33, 0x22, 0xFF] * (16 * 16) + [0x00] * 64)

with open(os.path.join(pub_dir, 'favicon.ico'), 'wb') as f:
    f.write(ico_bytes)
with open(os.path.join(root_dir, 'favicon.ico'), 'wb') as f:
    f.write(ico_bytes)
print("Created favicon.ico")

# 5. Create public/robots.txt
robots_txt = '''User-agent: *
Allow: /
'''
with open(os.path.join(pub_dir, 'robots.txt'), 'w', encoding='utf-8') as f:
    f.write(robots_txt)
print("Created public/robots.txt")

# 6. Create public/404.html
page_404 = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Poker Chess - 404 Not Found</title>
    <link rel="icon" type="image/svg+xml" href="favicon.svg">
    <style>
        body {
            margin: 0;
            padding: 0;
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            background: radial-gradient(circle at center, #173d2a 0%, #0a130f 90%);
            color: #f0f3f1;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            text-align: center;
        }
        .container {
            max-width: 480px;
            padding: 36px 24px;
            background: #15271e;
            border: 2px solid #d4af37;
            border-radius: 12px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.8), 0 0 20px rgba(212,175,55,0.3);
        }
        h1 {
            color: #d4af37;
            font-size: 2.4rem;
            margin: 0 0 12px 0;
        }
        p {
            font-size: 1rem;
            color: #d8e2dc;
            line-height: 1.6;
            margin-bottom: 24px;
        }
        a {
            display: inline-block;
            padding: 10px 28px;
            background: linear-gradient(135deg, #d4af37 0%, #aa841c 100%);
            color: #0b130e;
            text-decoration: none;
            font-weight: 800;
            border-radius: 6px;
            transition: transform 0.15s ease;
        }
        a:hover {
            transform: translateY(-2px);
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>404</h1>
        <p>The tactical quadrant you are searching for does not exist on this battlefield.</p>
        <a href="./">Return to Poker Chess</a>
    </div>
</body>
</html>
'''
with open(os.path.join(pub_dir, '404.html'), 'w', encoding='utf-8') as f:
    f.write(page_404)
print("Created public/404.html")

# 7. Create public/_headers (for Cloudflare Pages / Netlify)
headers_content = '''# Security and Caching Headers for Poker Chess

/*
  X-Content-Type-Options: nosniff
  X-Frame-Options: SAMEORIGIN
  Referrer-Policy: strict-origin-when-cross-origin
  Content-Security-Policy: default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; media-src 'self' data:; connect-src 'self'; font-src 'self'; object-src 'none'; base-uri 'self';

/*.html
  Cache-Control: no-cache, no-store, must-revalidate

/
  Cache-Control: no-cache, no-store, must-revalidate

/*.js
  Cache-Control: public, max-age=31536000, immutable

/*.css
  Cache-Control: public, max-age=31536000, immutable

/*.svg
  Cache-Control: public, max-age=31536000, immutable

/*.ico
  Cache-Control: public, max-age=31536000, immutable
'''
with open(os.path.join(pub_dir, '_headers'), 'w', encoding='utf-8') as f:
    f.write(headers_content)
print("Created public/_headers")

# 8. Create root LICENSE (MIT)
license_content = '''MIT License

Copyright (c) 2026 Poker Chess Authors

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
'''
with open(os.path.join(root_dir, 'LICENSE'), 'w', encoding='utf-8') as f:
    f.write(license_content)
print("Created root LICENSE")

# 9. Create root .gitignore
gitignore_content = '''# Python
__pycache__/
*.py[cod]
*$py.class
*.log

# OS generated
.DS_Store
Thumbs.db
desktop.ini

# Temporary and test artifacts
*.tmp
audit_*.py
tournament_smoke_test.py

# Node & Cloudflare
node_modules/
.wrangler/
'''
with open(os.path.join(root_dir, '.gitignore'), 'w', encoding='utf-8') as f:
    f.write(gitignore_content)
print("Created root .gitignore")

# 10. Create root README.md (Bilingual en/zh)
readme_content = '''# Poker Chess (扑克军棋 / 扑克将棋军棋)

> **English** | [中文说明](#中文说明)

An imperfect-information tactical browser board game combining the fog-of-war secrecy of **Chinese Military Chess (Junqi / 军棋)**, the piece-drop mechanics of **Japanese Shogi (将棋)**, and standard **Poker card hierarchy**.

Zero dependencies. Pure modern HTML5 / ES6+ JavaScript. No build step required.

---

## Features
- **True Fog-of-War**: Unrevealed enemy pieces remain completely face-down until engaged in combat.
- **Shogi Mochigoma Drops (打入)**: Captured enemy cards can be dropped back into your camp as Conscript Sappers.
- **Anti-Mutiny Ceiling**: Conscripts in hand and on board cannot exceed your living native forces.
- **Treason Execution Rule**: Conscripts are executed directly upon clash or defeat; no endless recapture loops.
- **Game Modes**:
  - **1v1**: $12 \\times 5$ board with secret setup (25 camp units + 2 secret reserves).
  - **4-Player (2v2 & FFA)**: $15 \\times 15$ Cross board with corner obstacles and alliance scoring.
  - **PvE**: 3 distinct offline CPU levels (**Low**, **Medium**, **High**).
  - **PvP**: Local pass-and-play on the same device.
- **Bilingual Interface**: Seamless instant toggling between English and Simplified Chinese (`zh`).
- **Web Audio Sound Effects**: Fully synthesized in-browser audio via the Web Audio API with zero external media files.

---

## Combat Hierarchy
1. **Joker (★ Flag / 军旗)**: Headquarters. Immobile. Captured = instant defeat.
2. **K (Bomb / 核弹)**: Moves 1 square orthogonally. Mutually destroys any enemy unit upon clash. Captures the Flag directly.
3. **Q, J (Landmines / 地雷)**: Immobile. Destroys any attacker except Sappers.
4. **10 to 2 (Officers / 军官)**: Numeric comparison ($10 > 9 > \\dots > 2$). Equal ranks mutually destroy each other. All officers defeat Sappers.
5. **A (Native Sappers / 主力工兵)**: Safely disarms and captures Landmines. Defeats Conscripts.
6. **Conscripts (战俘动员兵)**: Captured enemy cards dropped into battle. Lowest rank; destroyed upon clash with another Conscript and sent directly to the graveyard.

---

## Running Locally

Poker Chess requires no compilation or package installation:
```bash
# Using Python 3 built-in server:
python server.py

# Or any static web server:
npx serve public/
```
Then visit `http://localhost:8000` in your web browser.

---

## Security & Transparency Notice
Poker Chess runs 100% client-side in the browser. While Fog-of-War is strictly maintained in the DOM and render tree (face-down cards do not leak ranks or IDs to the HTML DOM), a determined user inspecting browser JavaScript memory can inspect local variables. As such, client-side anti-cheat is not claimed.

---

## License
Distributed under the [MIT License](LICENSE).

---

<a name="中文说明"></a>
# 中文说明

**扑克军棋** 是一款结合了**军棋暗棋机制**（战争迷雾与未知身份）、**日本将棋打入法则**（战俘重新空降部署）以及**扑克牌点数体系**的策略网页战棋游戏。

纯原生现代 ES6+ 与 HTML5 开发，零第三方依赖，无需任何构建或编译流程。

## 游戏核心机制
- **暗棋战争迷雾**：未交战敌军卡牌全暗置，绝不在前端 DOM 泄露任何点数或花色。
- **战俘空降（将棋打入）**：俘获的敌方棋子可作为**战俘工兵**空降部署至本方大营。
- **兵变法则（Anti-Mutiny）**：所持战俘总数（手牌+棋盘）不得超过本方存活主力人数。
- **叛军处决法则**：投敌的动员兵一旦阵亡或与敌方动员兵拼杀，双双就地处决送入墓地，严禁无限循环招降。
- **对局模式**：
  - **1v1 经典对决**：$12 \\times 5$ 棋盘，25张大营暗置主力 + 2张秘密底牌。
  - **四人争霸（2v2 组队与 1v1v1v1 混战）**：$15 \\times 15$ 十字大棋盘。
  - **单机人机（PvE）**：支持**初级 (Low)**、**中级 (Medium)**、**高级 (High)** 三种 AI 难度。
  - **同屏双人（PvP）**：支持同台设备即面轮换对弈。
- **双语支持**：中文与英文一键无缝热切换。
- **原生音效**：基于 Web Audio API 纯代码实时合成音效，无任何外部音频资源加载负担。

## 本地启动
```bash
python server.py
```
启动后浏览器自动打开 `http://localhost:8000` 即可开始对局。

## 开源协议
本项目采用 [MIT 许可证](LICENSE) 开源。
'''

with open(os.path.join(root_dir, 'README.md'), 'w', encoding='utf-8') as f:
    f.write(readme_content)
print("Created bilingual README.md")

print("\n[SUCCESS] Packaging completed successfully!")

