# Changelog

All notable changes to **Poker Chess** will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.0.0] - 2026-11-05

### Added
- **Core Game Modes**:
  - 1v1 Classic Battle on $12 \times 5$ board with 25 camp cards and 2 secret reserve cards.
  - 4-Player Battle (2v2 Alliance and 1v1v1v1 FFA) on $15 \times 15$ Cross board with corner obstacles.
  - PvE Single-Player mode featuring three distinct offline CPU difficulty levels: **Low**, **Medium**, and **High**.
  - PvP Same-Device Mode (pass-and-play).
- **Tactical Hybrid Mechanics**:
  - **Fog-of-War (暗棋)**: Unengaged enemy pieces remain face-down; identities revealed upon combat clash.
  - **Shogi Mochigoma Drops (打入)**: Captured enemy cards can be redeployed into your camp as Conscript Sappers.
  - **Anti-Mutiny Ceiling (兵变法则)**: Conscript forces in hand and on the board cannot exceed living native soldiers.
  - **Treason Execution Rule (叛军处决)**: Defeated conscripts are executed directly to the graveyard to prevent infinite loops.
- **Audio & Visual Interface**:
  - Zero-dependency sound synthesizer powered by the Web Audio API with mobile first-gesture auto-unlock.
  - Luxury felt baize aesthetic with three customizable themes: **Felt Green**, **Mahogany Wood**, and **Obsidian Dark**.
  - Two card display styles: **Art Mode** (traditional French deck illustration) and **Simplified Mode** (crisp strategic typography).
  - Bilingual interface supporting instant live toggling between **English** and **Simplified Chinese** (`zh`).
  - Strict **Simple & Clean** navigation invariant: active battle header contains exactly 3 uniform buttons (`Settings`, `New Game`, `Homepage`).
- **Production Hardening**:
  - Exception-safe `localStorage` wrapper protecting Safari private browsing and restricted cookie modes from `SecurityError` crashes.
  - Replaced synchronous `alert()` calls with sleek, non-blocking toast notifications and dedicated game over dialogs.
  - Added SVG data-URI favicon, Open Graph, and Twitter summary metadata for social sharing.
  - Mobile touch ergonomics: `touch-action: manipulation` and responsive board scaling for screens under 720px height.
  - Zero-build GitHub Actions workflow deploying the isolated `public/` bundle with two-tier immutable asset caching (`?v=1.0.0`).
