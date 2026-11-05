import asyncio
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.request
import websockets

sys.stdout.reconfigure(encoding='utf-8')

async def test_player_flow():
    tmp_dir = tempfile.mkdtemp(prefix="chrome_test_")
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
        print(f"Discovered {len(pages)} targets.")
        page = [p for p in pages if p.get('type') == 'page'][0]
        ws_url = page['webSocketDebuggerUrl']
        print(f"Connecting to: {ws_url}")

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
                    print(f"❌ JS EXCEPTION on `{expr}`: {res['exceptionDetails']}")
                    return None
                return res.get('result', {}).get('value')

            # Enable Page and Console
            await send('Page.enable')
            await send('Runtime.enable')

            # Navigate to localhost:8000
            print("Navigating to http://localhost:8000 ...")
            await send('Page.navigate', {'url': 'http://localhost:8000'})
            await asyncio.sleep(2)

            # Check readyState and title
            title = await eval_js("document.title")
            ready = await eval_js("document.readyState")
            url = await eval_js("window.location.href")
            print(f"Page title: '{title}', readyState: '{ready}', url: '{url}'")

            # Check if any errors occurred
            doc_body_snippet = await eval_js("document.body.innerHTML.substring(0, 200)")
            print(f"Body snippet: {doc_body_snippet}")

            print("--- STEP 1: Verify Initial Page State ---")
            home_display = await eval_js("document.getElementById('homepageScreen')?.style.display")
            game_display = await eval_js("document.getElementById('gameScreen')?.style.display")
            print(f"Homepage display: '{home_display}' | Game display: '{game_display}'")

            print("--- STEP 2: Player clicks 'Launch PvE Battle' ---")
            click_res = await eval_js("""
                (() => {
                    const btn = document.getElementById('launchPveBtn');
                    if (!btn) return 'NO_PVE_BTN';
                    btn.click();
                    return 'CLICKED_PVE';
                })()
            """)
            print(f"Launch PvE click result: {click_res}")
            await asyncio.sleep(0.5)

            home_display = await eval_js("document.getElementById('homepageScreen')?.style.display")
            game_display = await eval_js("document.getElementById('gameScreen')?.style.display")
            print(f"After Launch PvE -> Homepage display: '{home_display}' | Game display: '{game_display}'")

            # Check game instance state
            state = await eval_js("""
                (() => {
                    if (!window.gameInstance) return 'NO_GAME_INSTANCE';
                    return {
                        mode: window.gameInstance.mode,
                        gameState: window.gameInstance.gameState,
                        setupPlayer: window.gameInstance.setupPlayer,
                        currentTurn: window.gameInstance.currentTurn,
                        humanSide: window.gameInstance.humanSide,
                        boardRows: window.gameInstance.board.length,
                        boardCols: window.gameInstance.board[0].length
                    };
                })()
            """)
            print(f"Game State after PvE enter: {json.dumps(state, indent=2)}")

            # Check Setup Toolbar visibility & buttons
            setup_vis = await eval_js("""
                (() => {
                    const st = document.getElementById('setupToolbar');
                    const sb = document.getElementById('statusBar');
                    return {
                        setupToolbarDisplay: st ? st.style.display : 'NOT_FOUND',
                        statusBarDisplay: sb ? sb.style.display : 'NOT_FOUND'
                    };
                })()
            """)
            print(f"Setup toolbar vs status bar: {setup_vis}")

            print("--- STEP 3: Player clicks Auto-Fill Preset ---")
            auto_res = await eval_js("""
                (() => {
                    const autoBtn = document.getElementById('setupAutoBtn');
                    if (!autoBtn) return 'NO_AUTO_BTN';
                    autoBtn.click();
                    return {
                        campCount: document.getElementById('setupCampCount')?.textContent,
                        reserveCount: document.getElementById('setupReserveCount')?.textContent,
                        unplacedCount: document.getElementById('setupUnplacedCount')?.textContent
                    };
                })()
            """)
            print(f"Auto-fill counts: {auto_res}")

            print("--- STEP 4: Player clicks Confirm & Battle ---")
            confirm_res = await eval_js("""
                (() => {
                    const confBtn = document.getElementById('setupConfirmBtn');
                    if (!confBtn) return 'NO_CONFIRM_BTN';
                    confBtn.click();
                    return {
                        gameState: window.gameInstance.gameState,
                        currentTurn: window.gameInstance.currentTurn,
                        setupToolbarDisplay: document.getElementById('setupToolbar')?.style.display,
                        statusBarDisplay: document.getElementById('statusBar')?.style.display
                    };
                })()
            """)
            print(f"Confirm battle result: {confirm_res}")

            # Check header buttons
            top_bar_btns = await eval_js("""
                (() => {
                    const bar = document.querySelector('#gameScreen .control-bar');
                    if (!bar) return [];
                    return Array.from(bar.querySelectorAll('button')).map(b => ({ id: b.id, text: b.textContent }));
                })()
            """)
            print(f"Top bar buttons: {top_bar_btns}")

            # Check Mutiny Caps in 1v1
            caps = await eval_js("""
                (() => {
                    const container = document.getElementById('mutinyCaps');
                    if (!container) return 'NO_CAPS_CONTAINER';
                    return Array.from(container.children).map(c => c.textContent.trim().replace(/\\s+/g, ' '));
                })()
            """)
            print(f"Mutiny Caps badges in 1v1: {caps}")

            print("--- STEP 5: Player tries to make a move on board ---")
            move_res = await eval_js("""
                (() => {
                    const g = window.gameInstance;
                    if (g.gameState !== 'playing') return 'NOT_PLAYING: ' + g.gameState;
                    // Find a red mobile piece
                    for (let r = 0; r < 5; r++) {
                        for (let c = 0; c < 5; c++) {
                            const card = g.board[r][c];
                            if (card && card.player === 'red' && !card.isImmobile) {
                                const moves = g.getLegalMoves(r, c);
                                if (moves.length > 0) {
                                    return {
                                        pieceAt: { r, c, rank: card.rank },
                                        legalMoves: moves
                                    };
                                }
                            }
                        }
                    }
                    return 'NO_MOBILE_PIECE';
                })()
            """)
            print(f"Board move test: {move_res}")

            print("--- STEP 6: Player clicks Homepage button ---")
            home_click = await eval_js("""
                (() => {
                    const homeBtn = document.getElementById('homeBtn');
                    if (!homeBtn) return 'NO_HOME_BTN';
                    homeBtn.click();
                    return {
                        homeDisplay: document.getElementById('homepageScreen')?.style.display,
                        gameDisplay: document.getElementById('gameScreen')?.style.display
                    };
                })()
            """)
            print(f"Return to home: {home_click}")

    finally:
        proc.terminate()
        try:
            shutil.rmtree(tmp_dir, ignore_errors=True)
        except:
            pass

asyncio.run(test_player_flow())
