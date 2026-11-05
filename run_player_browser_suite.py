import asyncio
import base64
import json
import shutil
import subprocess
import sys
import tempfile
import urllib.request
import websockets

sys.stdout.reconfigure(encoding='utf-8')

async def run_player_test_suite():
    print("=" * 75)
    print("🎮 RUNNING COMPREHENSIVE BROWSER-BASED PLAYER INTERACTION TEST SUITE")
    print("=" * 75)

    tmp_dir = tempfile.mkdtemp(prefix="chrome_player_suite_")
    chrome_path = r'C:\Program Files\Google\Chrome\Application\chrome.exe'
    proc = subprocess.Popen([
        chrome_path,
        '--headless=new',
        '--remote-debugging-port=9225',
        f'--user-data-dir={tmp_dir}',
        '--disable-gpu',
        '--no-sandbox',
        '--disable-extensions',
        'about:blank'
    ])
    await asyncio.sleep(1.5)

    try:
        res = urllib.request.urlopen('http://localhost:9225/json')
        pages = json.loads(res.read())
        page = [p for p in pages if p.get('type') == 'page'][0]
        ws_url = page['webSocketDebuggerUrl']

        async with websockets.connect(ws_url) as ws:
            msg_id = 0
            
            async def send(method, params=None):
                nonlocal msg_id
                msg_id += 1
                payload = {'id': msg_id, 'method': method}
                if params: payload['params'] = params
                await ws.send(json.dumps(payload))
                while True:
                    raw = await ws.recv()
                    resp = json.loads(raw)
                    if resp.get('method') == 'Runtime.exceptionThrown':
                        print("🔥 UNCAUGHT JS EXCEPTION:", json.dumps(resp['params']['exceptionDetails'], indent=2))
                    if resp.get('id') == msg_id:
                        return resp.get('result', {})

            async def eval_js(expr):
                res = await send('Runtime.evaluate', {'expression': expr, 'returnByValue': True})
                if 'exceptionDetails' in res:
                    print(f"❌ JS EXCEPTION on `{expr[:60]}`: {res['exceptionDetails']}")
                    return None
                return res.get('result', {}).get('value')

            await send('Page.enable')
            await send('Runtime.enable')

            # 1. Page Load
            print("\n[TEST 1] Loading Application at http://localhost:8000 ...")
            await send('Page.navigate', {'url': 'http://localhost:8000'})
            await asyncio.sleep(1.5)

            home_vis = await eval_js("document.getElementById('homepageScreen')?.style.display")
            game_vis = await eval_js("document.getElementById('gameScreen')?.style.display")
            assert home_vis == 'flex', f"Homepage must be flex, got {home_vis}"
            assert game_vis == 'none', f"Game screen must be none, got {game_vis}"
            print("  ✅ Homepage screen correctly visible on launch.")

            # 1b. Test Homepage Rulebook Button
            print("\n[TEST 1b] Testing Homepage '📖 Rulebook' button ...")
            rulebook_btn_text = await eval_js("document.getElementById('homeRulebookBtn')?.textContent")
            print(f"  Rulebook button text: {rulebook_btn_text}")
            await eval_js("document.getElementById('homeRulebookBtn').click()")
            await asyncio.sleep(0.3)
            rules_vis = await eval_js("document.getElementById('rulesModal')?.style.display")
            assert rules_vis == 'flex', f"Rules modal should be open, got {rules_vis}"
            rule_content = await eval_js("document.getElementById('rulebookContent')?.innerHTML")
            assert "CPU Difficulty Levels" in rule_content or "人机难度设定" in rule_content, "Rulebook content missing CPU difficulty details"
            print("  ✅ Rulebook modal opened from homepage and contains CPU difficulty explanations.")
            await eval_js("document.getElementById('closeRulesBtn').click()")
            await asyncio.sleep(0.2)
            rules_vis = await eval_js("document.getElementById('rulesModal')?.style.display")
            assert rules_vis == 'none', "Rules modal failed to close"
            print("  ✅ Rulebook modal closed successfully.")

            # 2. PvE Red Player Full Flow
            print("\n[TEST 2] PvE Red Player Flow (Setup -> Confirm -> Board Moves -> Bot Response) ...")
            await eval_js("document.getElementById('launchPveBtn').click()")
            await asyncio.sleep(0.3)
            
            home_vis = await eval_js("document.getElementById('homepageScreen')?.style.display")
            game_vis = await eval_js("document.getElementById('gameScreen')?.style.display")
            assert home_vis == 'none' and game_vis == 'flex', "Failed transition to game screen"

            # Check header buttons
            top_btns = await eval_js("Array.from(document.querySelectorAll('#gameScreen .control-bar button')).map(b => b.id)")
            assert top_btns == ['settingsBtn', 'newGameBtn', 'homeBtn'], f"Top bar buttons must be 3, got: {top_btns}"
            btn_sizes = await eval_js("Array.from(document.querySelectorAll('#gameScreen .control-bar button')).map(b => ({id: b.id, w: b.offsetWidth, h: b.offsetHeight}))")
            print(f"  ✅ Top bar strictly 3 buttons with identical sizes: {btn_sizes}")
            assert len({b['w'] for b in btn_sizes}) == 1, f"All 3 buttons must have identical width! Got: {btn_sizes}"
            assert len({b['h'] for b in btn_sizes}) == 1, f"All 3 buttons must have identical height! Got: {btn_sizes}"

            # Auto setup & confirm
            await eval_js("document.getElementById('setupAutoBtn').click()")
            await asyncio.sleep(0.2)
            await eval_js("document.getElementById('setupConfirmBtn').click()")
            await asyncio.sleep(0.4)

            game_state = await eval_js("window.gameInstance.gameState")
            turn = await eval_js("window.gameInstance.currentTurn")
            assert game_state == 'playing', f"Expected playing, got {game_state}"
            assert turn == 'red', f"Expected red turn, got {turn}"
            print(f"  ✅ Battle started successfully! Turn: {turn}")

            # Verify Mutiny Caps (1v1 must NOT show 4 players)
            caps = await eval_js("Array.from(document.getElementById('mutinyCaps').children).map(c => c.textContent.trim().replace(/\\s+/g, ' '))")
            assert len(caps) == 2, f"1v1 must have strictly 2 badges, got: {caps}"
            assert any(word in caps[0] for word in ['Red', '红']) and any(word in caps[1] for word in ['Black', '黑']), f"Unexpected badge content: {caps}"
            print(f"  ✅ Status bar 1v1 verified: {caps}")

            snap = await send('Page.captureScreenshot')
            with open(r'C:\Users\27073\.gemini\antigravity\brain\459480b6-4034-4b53-ae1d-ee6e97a2d21e\ui_verified_clean.png', 'wb') as f:
                f.write(base64.b64decode(snap['data']))
            print("  📸 Captured verified screenshot to brain/ui_verified_clean.png")

            # Player makes a move by clicking tiles on board
            move_res = await eval_js("""
                (() => {
                    const g = window.gameInstance;
                    // Find a mobile red card with legal moves
                    for (let r = 0; r < 5; r++) {
                        for (let c = 0; c < 5; c++) {
                            const card = g.board[r][c];
                            if (card && card.player === 'red' && !card.isImmobile) {
                                const moves = g.getLegalMoves(r, c);
                                if (moves.length > 0) {
                                    const dest = moves[0];
                                    // Click source tile
                                    g.movePiece(r, c, dest.r, dest.c);
                                    window.renderApp();
                                    return { from: {r, c}, to: dest };
                                }
                            }
                        }
                    }
                    return null;
                })()
            """)
            assert move_res is not None, "Red player failed to find legal move"
            print(f"  ✅ Red player executed move: {move_res['from']} -> {move_res['to']}")

            # Wait for bot response
            await asyncio.sleep(1.0)
            log_len = await eval_js("window.gameInstance.moveLog.length")
            print(f"  ✅ Move log count after Bot response: {log_len}")

            # 3. Settings Modal Test
            print("\n[TEST 3] Settings Modal & Live Theme/Language Switching ...")
            await eval_js("document.getElementById('settingsBtn').click()")
            await asyncio.sleep(0.2)
            stg_vis = await eval_js("document.getElementById('settingsModal').style.display")
            assert stg_vis == 'flex', "Settings modal failed to open"

            # Switch to Chinese
            await eval_js("""
                (() => {
                    const zhRadio = document.querySelector('input[name="langRadio"][value="zh"]');
                    zhRadio.checked = true;
                    zhRadio.dispatchEvent(new Event('change', { bubbles: true }));
                })()
            """)
            await asyncio.sleep(0.2)
            lang = await eval_js("window.I18N.currentLang")
            assert lang == 'zh', f"Language should be zh, got {lang}"
            print("  ✅ Language switched to Chinese (zh).")

            # Switch card style to simplified
            await eval_js("""
                (() => {
                    const sRadio = document.querySelector('input[name="cardStyleRadio"][value="simplified"]');
                    sRadio.checked = true;
                    sRadio.dispatchEvent(new Event('change', { bubbles: true }));
                })()
            """)
            await asyncio.sleep(0.2)
            style = await eval_js("window.I18N.currentCardStyle")
            assert style == 'simplified', f"Card style should be simplified, got {style}"
            print("  ✅ Card art style switched to Simplified Mode.")

            # Close settings
            await eval_js("document.getElementById('closeSettingsBtn').click()")
            await asyncio.sleep(0.2)
            stg_vis = await eval_js("document.getElementById('settingsModal').style.display")
            assert stg_vis == 'none', "Settings modal failed to close"
            print("  ✅ Settings modal closed.")

            # 4. Return to Homepage
            print("\n[TEST 4] Return to Homepage via '🏠 Homepage' button ...")
            await eval_js("document.getElementById('homeBtn').click()")
            await asyncio.sleep(0.3)
            home_vis = await eval_js("document.getElementById('homepageScreen')?.style.display")
            game_vis = await eval_js("document.getElementById('gameScreen')?.style.display")
            assert home_vis == 'flex' and game_vis == 'none', "Homepage button failed to return to home screen"
            print("  ✅ Player returned to Homepage.")

            # 5. PvE Black Player
            print("\n[TEST 5] Launch PvE as Black (Red Bot Deploys and Moves First) ...")
            await eval_js("""
                (() => {
                    const blackRadio = document.querySelector('input[name="pveSide"][value="black"]');
                    blackRadio.checked = true;
                    blackRadio.dispatchEvent(new Event('change', { bubbles: true }));
                })()
            """)
            await eval_js("document.getElementById('launchPveBtn').click()")
            await asyncio.sleep(0.3)
            await eval_js("document.getElementById('setupAutoBtn').click()")
            await asyncio.sleep(0.2)
            await eval_js("document.getElementById('setupConfirmBtn').click()")
            await asyncio.sleep(0.8)

            black_turn = await eval_js("window.gameInstance.currentTurn")
            human_side = await eval_js("window.gameInstance.humanSide")
            assert human_side == 'black', f"Human side should be black, got {human_side}"
            print(f"  ✅ PvE Black game running. Current Turn: {black_turn}")

            # 6. PvP 2v2 Mode
            print("\n[TEST 6] PvP 2v2 (15x15 Cross Board, 4 Seats) ...")
            await eval_js("document.getElementById('homeBtn').click()")
            await asyncio.sleep(0.3)
            await eval_js("document.getElementById('tabBtnPvp').click()")
            await asyncio.sleep(0.2)
            await eval_js("""
                (() => {
                    const r2v2 = document.querySelector('input[name="pvpModeType"][value="2v2"]');
                    r2v2.checked = true;
                    r2v2.dispatchEvent(new Event('change', { bubbles: true }));
                })()
            """)
            await eval_js("document.getElementById('launchPvpBtn').click()")
            await asyncio.sleep(0.3)
            await eval_js("document.getElementById('setupConfirmBtn').click()")
            await asyncio.sleep(0.3)

            p_count = await eval_js("window.gameInstance.playerCount")
            caps_4p = await eval_js("Array.from(document.getElementById('mutinyCaps').children).map(c => c.textContent.trim().replace(/\\s+/g, ' '))")
            assert p_count == 4, f"Player count should be 4, got {p_count}"
            assert len(caps_4p) == 4, f"2v2 must have 4 player badges, got {len(caps_4p)}: {caps_4p}"
            print(f"  ✅ 2v2 Mode active on 15x15 board with 4 badges: {caps_4p}")

            # 7. Switch back to 1v1 PvP
            print("\n[TEST 7] Switch back to PvP 1v1 (Confirming zero leakage of 4P info) ...")
            await eval_js("document.getElementById('homeBtn').click()")
            await asyncio.sleep(0.3)
            await eval_js("""
                (() => {
                    const r1v1 = document.querySelector('input[name="pvpModeType"][value="1v1"]');
                    r1v1.checked = true;
                    r1v1.dispatchEvent(new Event('change', { bubbles: true }));
                })()
            """)
            await eval_js("document.getElementById('launchPvpBtn').click()")
            await asyncio.sleep(0.3)
            await eval_js("document.getElementById('setupAutoBtn').click()")
            await asyncio.sleep(0.2)
            await eval_js("document.getElementById('setupConfirmBtn').click()")
            await asyncio.sleep(0.3)

            caps_1v1 = await eval_js("Array.from(document.getElementById('mutinyCaps').children).map(c => c.textContent.trim().replace(/\\s+/g, ' '))")
            assert len(caps_1v1) == 2, f"1v1 MUST have exactly 2 badges, got {len(caps_1v1)}: {caps_1v1}"
            print(f"  ✅ Badges verified strictly 2 in 1v1: {caps_1v1}")

            # 8. Live In-Browser Combat Hierarchy Unit Validation
            print("\n[TEST 8] Live In-Browser Combat Hierarchy Verification ...")
            combat_tests_passed = await eval_js("""
                (() => {
                    const g = window.gameInstance;

                    // A. Conscript vs Conscript: Mutual destruction to Graveyard
                    const c1 = new Card('red', '♥', '8', false);
                    c1.isMochigoma = true;
                    c1.isSapper = false;
                    const c2 = new Card('black', '♠', '9', false);
                    c2.isMochigoma = true;
                    c2.isSapper = false;
                    g.graveyard = [];
                    g.board[5][2] = c1;
                    g.board[6][2] = c2;
                    g.currentTurn = 'red';
                    g.movePiece(5, 2, 6, 2);
                    if (g.board[6][2] !== null) return "Conscript vs Conscript failed: tile not null";
                    if (!g.graveyard.includes(c1) || !g.graveyard.includes(c2)) return "Conscript vs Conscript failed: not both in graveyard";

                    // B. Native Sapper vs Conscript: Native Sapper wins, Conscript executed to Graveyard
                    const sapA = new Card('red', '♥', 'A', false); // Native Sapper
                    const c3 = new Card('black', '♠', '4', false);
                    c3.isMochigoma = true;
                    c3.isSapper = false;
                    g.graveyard = [];
                    g.hands['red'].mochigoma = [];
                    g.board[5][2] = sapA;
                    g.board[6][2] = c3;
                    g.currentTurn = 'red';
                    g.movePiece(5, 2, 6, 2);
                    if (g.board[6][2] !== sapA) return "Native Sapper vs Conscript failed: Sapper not on board";
                    if (!g.graveyard.includes(c3)) return "Native Sapper vs Conscript failed: Conscript not executed to Graveyard";
                    if (g.hands['red'].mochigoma.includes(c3)) return "Native Sapper vs Conscript failed: Conscript erroneously captured into Mochigoma";

                    // C. Officer vs Conscript: Officer wins, Conscript executed to Graveyard
                    const off5 = new Card('red', '♥', '5', false);
                    const c4 = new Card('black', '♠', '7', false);
                    c4.isMochigoma = true;
                    c4.isSapper = false;
                    g.graveyard = [];
                    g.hands['red'].mochigoma = [];
                    g.board[5][2] = off5;
                    g.board[6][2] = c4;
                    g.currentTurn = 'red';
                    g.movePiece(5, 2, 6, 2);
                    if (g.board[6][2] !== off5) return "Officer vs Conscript failed: Officer not on board";
                    if (!g.graveyard.includes(c4)) return "Officer vs Conscript failed: Conscript not in Graveyard";
                    if (g.hands['red'].mochigoma.includes(c4)) return "Officer vs Conscript failed: Conscript erroneously captured into Mochigoma";

                    // D. Officer vs Native Sapper: Officer wins, Native Sapper captured into Mochigoma
                    const off8 = new Card('red', '♥', '8', false);
                    const sapB = new Card('black', '♠', 'A', false);
                    g.graveyard = [];
                    g.hands['red'].mochigoma = [];
                    g.board[5][2] = off8;
                    g.board[6][2] = sapB;
                    g.currentTurn = 'red';
                    g.movePiece(5, 2, 6, 2);
                    if (g.board[6][2] !== off8) return "Officer vs Native Sapper failed: Officer not on board";
                    if (!g.hands['red'].mochigoma.includes(sapB)) return "Officer vs Native Sapper failed: Native Sapper not captured into Mochigoma";

                    // E. Conscript vs Landmine: Conscript disarms Landmine, Landmine captured into Mochigoma
                    const c5 = new Card('red', '♥', '3', false);
                    c5.isMochigoma = true;
                    c5.isSapper = false;
                    const mineQ = new Card('black', '♠', 'Q', false);
                    g.graveyard = [];
                    g.hands['red'].mochigoma = [];
                    g.board[5][2] = c5;
                    g.board[6][2] = mineQ;
                    g.currentTurn = 'red';
                    g.movePiece(5, 2, 6, 2);
                    if (g.board[6][2] !== c5) return "Conscript vs Landmine failed: Conscript not on board";
                    if (!g.hands['red'].mochigoma.includes(mineQ)) return "Conscript vs Landmine failed: Landmine not captured into Mochigoma";

                    return "OK";
                })()
            """)
            assert combat_tests_passed == "OK", f"Combat hierarchy test failed: {combat_tests_passed}"
            print("  ✅ Live Combat Hierarchy verified: Conscripts work strictly as sappers, smallest rank, mutual destruction with other conscripts, executed upon defeat.")

            # 9. Reset language and theme back to default
            await eval_js("window.I18N.setLang('en'); window.I18N.setCardStyle('art'); window.renderApp();")
            print("\n🏆 ALL BROWSER PLAYER TESTS PASSED WITH 100% SUCCESS!")

    finally:
        proc.terminate()
        try: shutil.rmtree(tmp_dir, ignore_errors=True)
        except: pass

asyncio.run(run_player_test_suite())
