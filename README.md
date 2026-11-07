# Poker Chess (扑克军棋)

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
  - **1v1**: $12 \times 5$ board with secret setup (25 camp units + 2 secret reserves).
  - **4-Player (2v2 & FFA)**: $15 \times 15$ Cross board with corner obstacles and alliance scoring.
  - **PvE**: 3 distinct offline CPU levels (**Low**, **Medium**, **High**).
  - **PvP**: Local pass-and-play on the same device.
- **Bilingual Interface**: Seamless instant toggling between English and Simplified Chinese (`zh`).
- **Web Audio Sound Effects**: Fully synthesized in-browser audio via the Web Audio API with zero external media files.

---

## Combat Hierarchy
1. **Joker (★ Flag / 军旗)**: Headquarters. Immobile. Captured = instant defeat.
2. **K (Bomb / 核弹)**: Moves 1 square orthogonally. Mutually destroys any enemy unit upon clash. Captures the Flag directly.
3. **Q, J (Landmines / 地雷)**: Immobile. Destroys any attacker except Sappers.
4. **10 to 2 (Officers / 军官)**: Numeric comparison ($10 > 9 > \dots > 2$). Equal ranks mutually destroy each other. All officers defeat Sappers.
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
  - **1v1 经典对决**：$12 \times 5$ 棋盘，25张大营暗置主力 + 2张秘密底牌。
  - **四人争霸（2v2 组队与 1v1v1v1 混战）**：$15 \times 15$ 十字大棋盘。
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
