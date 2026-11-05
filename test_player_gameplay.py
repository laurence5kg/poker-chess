import asyncio
import json
import shutil
import subprocess
import sys
import tempfile
import urllib.request
import websockets

sys.stdout.reconfigure(encoding='utf-8')

async def test_full_player_gameplay():
    tmp_dir = tempfile.mkdtemp(prefix="chrome_play_")
    chrome_path = r'C:\Program Files\Google\Chrome\Application\chrome.exe'
    proc = subprocess.Popen([
        chrome_path,
        '--headless=new',
        '--remote-debugging-port=9222',
        f'--user-data-dir={tmp_dir}',
        '--disable-gpu',
        '--no-sandbox',
        '--disable-extensions',
        'about:blank'
    ])
    await asyncio.sleep(1.5)

    try:
        res = urllib.request.urlopen('http://localhost:9222/json')
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

            print("1. Navigating to http://localhost:8000 ...")
            await send('Page.navigate', {'url': 'http://localhost:8000'})
            await asyncio.sleep(1.5)

            # TEST A: PvE Red Player full move & bot response
            print("\n--- TEST A: PvE Red Player moves, AI bot responds ---")
            await eval_js("document.getElementById('launchPveBtn').click()")
            await asyncio.sleep(0.3)
            await eval_js("document.getElementById('setupAutoBtn').click()")
            await asyncio.sleep(0.3)
            await eval_js("document.getElementById('setupConfirmBtn').click()")
            await asyncio.sleep(0.3)

            turn1 = await eval_js("window.gameInstance.currentTurn")
            print(f"Initial Turn: {turn1}")

            # Find a legal move for Red
            move_res = await eval_js("""
                (() => {
                    const g = window.gameInstance;
                    for (let r = 0; r < 5; r++) {
                        for (let c = 0; c < 5; c++) {
                            const card = g.board[r][c];
                            if (card && card.player === 'red' && !card.isImmobile) {
                                const moves = g.getLegalMoves(r, c);
                                if (moves.length > 0) {
                                    // Click to select
                                    const tileFrom = document.querySelectorAll('#boardGrid .tile')[r * 5 + c];
                                    // Wait, let's find the tile
                                    g.selectedTile = { r, c };
                                    window.renderApp();
                                    const dest = moves[0];
                                    g.executeMove(r, c, dest.r, dest.c);
                                    window.renderApp();
                                    return { from: {r, c}, to: dest, rank: card.rank, role: card.roleName };
                                }
                            }
                        }
                    }
                    return null;
                })()
            """)
            print(f"Human Red move executed: {move_res}")

            # Let Bot take its turn if triggered
            await asyncio.sleep(1.0)
            state_after_bot = await eval_js("""
                (() => {
                    const g = window.gameInstance;
                    return {
                        currentTurn: g.currentTurn,
                        moveLogLength: g.moveLog.length,
                        lastLog: g.moveLog[g.moveLog.length - 1]?.text
                    };
                })()
            """)
            print(f"State after Red move + Bot response: {state_after_bot}")

            # TEST B: Return to Homepage and launch PvE as Black Player
            print("\n--- TEST B: PvE Black Player (Red Bot moves first) ---")
            await eval_js("document.getElementById('homeBtn').click()")
            await asyncio.sleep(0.3)

            # Select Black radio on homepage
            await eval_js("""
                (() => {
                    const blackRadio = document.querySelector('input[name="pveSide"][value="black"]');
                    if (blackRadio) {
                        blackRadio.checked = true;
                        blackRadio.dispatchEvent(new Event('change', { bubbles: true }));
                    }
                })()
            """)
            await eval_js("document.getElementById('launchPveBtn').click()")
            await asyncio.sleep(0.3)

            # Player Black auto-deploys
            await eval_js("document.getElementById('setupAutoBtn').click()")
            await asyncio.sleep(0.3)
            await eval_js("document.getElementById('setupConfirmBtn').click()")
            await asyncio.sleep(0.8)

            pve_black_state = await eval_js("""
                (() => {
                    const g = window.gameInstance;
                    return {
                        mode: g.mode,
                        humanSide: g.humanSide,
                        botSide: g.botSide,
                        gameState: g.gameState,
                        currentTurn: g.currentTurn,
                        moveLogCount: g.moveLog.length,
                        lastLog: g.moveLog[g.moveLog.length - 1]?.text
                    };
                })()
            """)
            print(f"PvE Black state: {pve_black_state}")

            # TEST C: Return to Homepage and test PvP 2v2
            print("\n--- TEST C: PvP 2v2 (15x15 Cross Board, 4 Players) ---")
            await eval_js("document.getElementById('homeBtn').click()")
            await asyncio.sleep(0.3)
            # Switch tab to PvP
            await eval_js("document.getElementById('tabBtnPvp').click()")
            await asyncio.sleep(0.3)
            # Select 2v2
            await eval_js("""
                (() => {
                    const r2v2 = document.querySelector('input[name="pvpModeType"][value="2v2"]');
                    r2v2.checked = true;
                    r2v2.dispatchEvent(new Event('change', { bubbles: true }));
                })()
            """)
            await asyncio.sleep(0.2)
            await eval_js("document.getElementById('launchPvpBtn').click()")
            await asyncio.sleep(0.3)

            # 4P starts auto-setup
            await eval_js("document.getElementById('setupConfirmBtn').click()")
            await asyncio.sleep(0.3)

            p2v2_state = await eval_js("""
                (() => {
                    const g = window.gameInstance;
                    const caps = Array.from(document.getElementById('mutinyCaps').children).map(c => c.textContent.trim().replace(/\\s+/g, ' '));
                    return {
                        mode: g.mode,
                        playerCount: g.playerCount,
                        fourPlayerMode: g.fourPlayerMode,
                        currentTurn: g.currentTurn,
                        capsCount: caps.length,
                        caps: caps
                    };
                })()
            """)
            print(f"2v2 State & Caps: {p2v2_state}")

            # TEST D: Return to Homepage and test PvP 1v1 (Ensure 4P info disappears!)
            print("\n--- TEST D: Switch from 2v2 back to 1v1 (Verify 4P badges NEVER leak into 1v1!) ---")
            await eval_js("document.getElementById('homeBtn').click()")
            await asyncio.sleep(0.3)
            # Switch back to 1v1
            await eval_js("""
                (() => {
                    const r1v1 = document.querySelector('input[name="pvpModeType"][value="1v1"]');
                    r1v1.checked = true;
                    r1v1.dispatchEvent(new Event('change', { bubbles: true }));
                })()
            """)
            await asyncio.sleep(0.2)
            await eval_js("document.getElementById('launchPvpBtn').click()")
            await asyncio.sleep(0.3)
            await eval_js("document.getElementById('setupAutoBtn').click()")
            await asyncio.sleep(0.3)
            await eval_js("document.getElementById('setupConfirmBtn').click()")
            await asyncio.sleep(0.3)

            p1v1_after_2v2_state = await eval_js("""
                (() => {
                    const g = window.gameInstance;
                    const caps = Array.from(document.getElementById('mutinyCaps').children).map(c => c.textContent.trim().replace(/\\s+/g, ' '));
                    return {
                        mode: g.mode,
                        playerCount: g.playerCount,
                        capsCount: caps.length,
                        caps: caps
                    };
                })()
            """)
            print(f"1v1 after 2v2 -> Caps Count: {p1v1_after_2v2_state['capsCount']} | Badges: {p1v1_after_2v2_state['caps']}")
            if p1v1_after_2v2_state['capsCount'] == 2:
                print("✅ VERIFIED: 1v1 has STRICTLY 2 army badges! 4-player badges did NOT leak!")
            else:
                print(f"❌ LEAK DETECTED: Expected 2 badges, got {p1v1_after_2v2_state['capsCount']}")

            # TEST E: Settings Modal from Game Screen
            print("\n--- TEST E: Settings Modal ---")
            await eval_js("document.getElementById('settingsBtn').click()")
            await asyncio.sleep(0.3)
            modal_vis = await eval_js("document.getElementById('settingsModal').style.display")
            print(f"Settings Modal Display: {modal_vis}")
            await eval_js("document.getElementById('closeSettingsBtn').click()")
            await asyncio.sleep(0.3)
            modal_vis_after = await eval_js("document.getElementById('settingsModal').style.display")
            print(f"Settings Modal Display after Done: {modal_vis_after}")

            # TEST F: New Game button inside game
            print("\n--- TEST F: 'New Game' button in game header ---")
            await eval_js("document.getElementById('newGameBtn').click()")
            await asyncio.sleep(0.3)
            new_game_state = await eval_js("""
                (() => {
                    const g = window.gameInstance;
                    return {
                        gameState: g.gameState,
                        setupToolbarVis: document.getElementById('setupToolbar')?.style.display
                    };
                })()
            """)
            print(f"New Game state: {new_game_state}")

    finally:
        proc.terminate()
        try: shutil.rmtree(tmp_dir, ignore_errors=True)
        except: pass

asyncio.run(test_full_player_gameplay())
