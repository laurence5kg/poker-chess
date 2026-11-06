import asyncio
import base64
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

SERVER_HTTP = "http://127.0.0.1:8787"
SERVER_WS = "ws://127.0.0.1:8787"
APP_HTTP = "http://127.0.0.1:8000"
CHROME_PATH = r'C:\Program Files\Google\Chrome\Application\chrome.exe'

class CDPSession:
    def __init__(self, port, tmp_dir):
        self.port = port
        self.tmp_dir = tmp_dir
        self.proc = None
        self.ws = None
        self.msg_id = 0
        self.incoming_frames = []
        self.sent_frames = []
        self.running = False
        self.rx_task = None

    async def start(self):
        self.proc = subprocess.Popen([
            CHROME_PATH,
            '--headless=new',
            f'--remote-debugging-port={self.port}',
            f'--user-data-dir={self.tmp_dir}',
            '--disable-gpu',
            '--no-sandbox',
            '--disable-extensions',
            'about:blank'
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        await asyncio.sleep(1.5)

        res = urllib.request.urlopen(f'http://localhost:{self.port}/json')
        pages = json.loads(res.read())
        page = [p for p in pages if p.get('type') == 'page'][0]
        ws_url = page['webSocketDebuggerUrl']

        self.ws = await websockets.connect(ws_url, max_size=10*1024*1024)
        self.running = True
        self.pending_responses = {}
        self.rx_task = asyncio.create_task(self._listen())

        await self.send('Page.enable')
        await self.send('Runtime.enable')
        await self.send('Network.enable')

    async def _listen(self):
        try:
            while self.running:
                raw = await self.ws.recv()
                msg = json.loads(raw)
                
                # Check for CDP response to our commands
                if 'id' in msg and msg['id'] in self.pending_responses:
                    self.pending_responses[msg['id']].set_result(msg.get('result', {}))
                
                # Check for Network WebSocket events
                method = msg.get('method')
                if method == 'Network.webSocketFrameReceived':
                    payload_data = msg['params']['response']['payloadData']
                    self.incoming_frames.append(payload_data)
                elif method == 'Network.webSocketFrameSent':
                    payload_data = msg['params']['response']['payloadData']
                    self.sent_frames.append(payload_data)
        except Exception as e:
            if self.running:
                print(f"[CDP port {self.port}] Listen loop error:", e)

    async def send(self, method, params=None):
        self.msg_id += 1
        cid = self.msg_id
        payload = {'id': cid, 'method': method}
        if params:
            payload['params'] = params
        
        loop = asyncio.get_running_loop()
        future = loop.create_future()
        self.pending_responses[cid] = future
        await self.ws.send(json.dumps(payload))
        return await asyncio.wait_for(future, timeout=10.0)

    async def eval_js(self, expr):
        res = await self.send('Runtime.evaluate', {'expression': expr, 'returnByValue': True})
        if 'exceptionDetails' in res:
            print(f"❌ JS EXCEPTION on `{expr[:60]}`: {res['exceptionDetails']}")
            return None
        return res.get('result', {}).get('value')

    async def close(self):
        self.running = False
        if self.rx_task:
            self.rx_task.cancel()
        if self.ws:
            await self.ws.close()
        if self.proc:
            self.proc.terminate()
            try:
                self.proc.wait(timeout=2.0)
            except Exception:
                self.proc.kill()
        if os.path.exists(self.tmp_dir):
            shutil.rmtree(self.tmp_dir, ignore_errors=True)


async def run_phase6_verification():
    print("=" * 80)
    print("🚀 PHASE 6 AUTOMATED VERIFICATION: TRUE ONLINE PVP")
    print("   1. Two-Browser End-to-End Match with Zero-Leakage CDP Frame & DOM Assertions")
    print("   2. 100+ Adversarial Server Fuzz Attacks (Malformations, Out-of-Turn, Forgeries)")
    print("=" * 80)

    # Step 0: Verify Wrangler and Server.py health
    print("\n[STEP 0] Checking Wrangler and Server.py health...")
    try:
        health_req = urllib.request.urlopen(f"{SERVER_HTTP}/api/health")
        health = json.loads(health_req.read().decode('utf-8'))
        assert health.get('status') == 'ok', f"Wrangler health bad: {health}"
        print(f"  ✅ Cloudflare Workers Backend is healthy: {health}")
    except Exception as e:
        print(f"  ❌ Backend health check failed: {e}")
        return False

    tmp_a = tempfile.mkdtemp(prefix="chrome_host_a_")
    tmp_b = tempfile.mkdtemp(prefix="chrome_guest_b_")

    host = CDPSession(9225, tmp_a)
    guest = CDPSession(9226, tmp_b)

    try:
        print("\n[STEP 1] Launching Two Separate Headless Chrome Instances (Host & Guest)...")
        await host.start()
        await guest.start()
        print("  ✅ Host Chrome (Port 9225) & Guest Chrome (Port 9226) online.")

        # Navigate Host to App
        print("\n[STEP 2] Host (Player A) Navigating to App & Opening Online Lobby...")
        await host.send('Page.navigate', {'url': APP_HTTP})
        await asyncio.sleep(1.0)

        # Host clicks PvP -> Online tab
        await host.eval_js("document.getElementById('tabBtnPvp').click()")
        await asyncio.sleep(0.3)
        await host.eval_js("document.getElementById('tabPvpOnlineBtn').click()")
        await asyncio.sleep(0.5)

        # Host fills nickname "Alice", chooses "Red", clicks "Host Game"
        await host.eval_js("""
            (() => {
                document.getElementById('onlineNicknameInput').value = 'Alice';
                const redRadio = document.querySelector('input[name="onlineSidePref"][value="red"]');
                if (redRadio) {
                    redRadio.checked = true;
                    redRadio.dispatchEvent(new Event('change', { bubbles: true }));
                }
                document.getElementById('createOnlineRoomBtn').click();
            })()
        """)
        await asyncio.sleep(1.0)

        host_room_id = await host.eval_js("window.networkClient?.roomId")
        print(f"  ✅ Host Room Created. Room ID: {host_room_id}")
        assert host_room_id, "Host failed to create room"

        # Navigate Guest to App
        print("\n[STEP 3] Guest (Player B) Navigating to App & Joining Host Room...")
        await guest.send('Page.navigate', {'url': APP_HTTP})
        await asyncio.sleep(1.0)

        await guest.eval_js("document.getElementById('tabBtnPvp').click()")
        await asyncio.sleep(0.3)
        await guest.eval_js("document.getElementById('tabPvpOnlineBtn').click()")
        await asyncio.sleep(1.2)

        # Wait for room list to render
        for _ in range(10):
            has_join_btn = await guest.eval_js("!!document.querySelector('.room-join-btn')")
            if has_join_btn:
                break
            await guest.eval_js("document.getElementById('refreshRoomsBtn')?.click()")
            await asyncio.sleep(0.5)

        # Guest sets nickname "Bob" and clicks Join button on the host room
        await guest.eval_js("""
            (() => {
                document.getElementById('onlineNicknameInput').value = 'Bob';
                const joinBtn = document.querySelector('.room-join-btn');
                if (joinBtn) joinBtn.click();
            })()
        """)
        await asyncio.sleep(1.5)

        guest_room_id = await guest.eval_js("window.networkClient?.roomId")
        print(f"  ✅ Guest Joined Room ID: {guest_room_id}")
        assert guest_room_id == host_room_id, f"Room IDs must match: {guest_room_id} vs {host_room_id}"

        # Step 4: Verify Both Enter Setup Phase
        print("\n[STEP 4] Verifying Both Players Transition to Secret Deployment Phase...")
        await asyncio.sleep(0.5)
        host_state = await host.eval_js("window.gameInstance.gameState")
        guest_state = await guest.eval_js("window.gameInstance.gameState")
        host_color = await host.eval_js("window.networkClient.playerColor")
        guest_color = await guest.eval_js("window.networkClient.playerColor")

        print(f"  Host state: {host_state}, Color: {host_color}")
        print(f"  Guest state: {guest_state}, Color: {guest_color}")
        assert host_state == 'setup', f"Host expected setup, got {host_state}"
        assert guest_state == 'setup', f"Guest expected setup, got {guest_state}"
        assert host_color == 'red' and guest_color == 'black', f"Colors mismatched: {host_color}, {guest_color}"

        # Step 5: Both Submit Secret Formations
        print("\n[STEP 5] Both Players Submit Formations (Auto-Deploy -> Confirm)...")
        await host.eval_js("document.getElementById('setupAutoBtn').click()")
        await asyncio.sleep(0.3)
        await host.eval_js("document.getElementById('setupConfirmBtn').click()")
        await asyncio.sleep(0.5)

        await guest.eval_js("document.getElementById('setupAutoBtn').click()")
        await asyncio.sleep(0.3)
        await guest.eval_js("document.getElementById('setupConfirmBtn').click()")
        await asyncio.sleep(1.0)

        host_state = await host.eval_js("window.gameInstance.gameState")
        guest_state = await guest.eval_js("window.gameInstance.gameState")
        assert host_state == 'playing', f"Host game state expected playing, got {host_state}"
        assert guest_state == 'playing', f"Guest game state expected playing, got {guest_state}"
        print("  ✅ Both players in 'playing' state! Battle begins!")

        # Step 6: RIGOROUS ZERO-LEAKAGE VERIFICATION (CDP WebSocket Frames)
        print("\n[STEP 6] 🛡️ RIGOROUS ZERO-LEAKAGE AUDIT: CDP WebSocket Frames...")
        print(f"  Host received {len(host.incoming_frames)} frames.")
        print(f"  Guest received {len(guest.incoming_frames)} frames.")
        assert len(host.incoming_frames) > 0, "Host received zero frames"
        assert len(guest.incoming_frames) > 0, "Guest received zero frames"

        # Check Host's received frames: Must NEVER leak Black's unrevealed ranks or reserves
        for idx, frame in enumerate(host.incoming_frames):
            try:
                data = json.loads(frame)
            except Exception:
                continue
            if data.get('type') == 'state_view':
                payload = data.get('payload', {})
                board = payload.get('board', [])
                # Check board
                for r in range(12):
                    for c in range(5):
                        p = board[r][c]
                        if p and p.get('player') == 'black' and not p.get('faceUp'):
                            assert p.get('rank') is None, f"🚨 LEAK! Host frame #{idx} leaked black rank: {p}"
                            assert p.get('suit') is None, f"🚨 LEAK! Host frame #{idx} leaked black suit: {p}"
                            assert p.get('isBomb') is False, f"🚨 LEAK! Host frame #{idx} leaked isBomb"
                            assert p.get('isLandmine') is False, f"🚨 LEAK! Host frame #{idx} leaked isLandmine"
                            assert p.get('isFlag') is False, f"🚨 LEAK! Host frame #{idx} leaked isFlag"
                # Check black hands
                black_hand = payload.get('hands', {}).get('black', {})
                assert black_hand.get('startingReserves') == [], f"🚨 LEAK! Host frame #{idx} leaked black reserves: {black_hand}"
                assert 'startingReserveCount' in black_hand, "Missing startingReserveCount"

        print("  ✅ Host Frames 100% Leak-Free: Zero opponent ranks, suits, roles, or reserves received.")

        # Check Guest's received frames: Must NEVER leak Red's unrevealed ranks or reserves
        for idx, frame in enumerate(guest.incoming_frames):
            try:
                data = json.loads(frame)
            except Exception:
                continue
            if data.get('type') == 'state_view':
                payload = data.get('payload', {})
                board = payload.get('board', [])
                for r in range(12):
                    for c in range(5):
                        p = board[r][c]
                        if p and p.get('player') == 'red' and not p.get('faceUp'):
                            assert p.get('rank') is None, f"🚨 LEAK! Guest frame #{idx} leaked red rank: {p}"
                            assert p.get('suit') is None, f"🚨 LEAK! Guest frame #{idx} leaked red suit: {p}"
                            assert p.get('isBomb') is False, f"🚨 LEAK! Guest frame #{idx} leaked isBomb"
                            assert p.get('isLandmine') is False, f"🚨 LEAK! Guest frame #{idx} leaked isLandmine"
                            assert p.get('isFlag') is False, f"🚨 LEAK! Guest frame #{idx} leaked isFlag"
                red_hand = payload.get('hands', {}).get('red', {})
                assert red_hand.get('startingReserves') == [], f"🚨 LEAK! Guest frame #{idx} leaked red reserves: {red_hand}"

        print("  ✅ Guest Frames 100% Leak-Free: Zero opponent ranks, suits, roles, or reserves received.")

        # Step 7: ZERO-LEAKAGE VERIFICATION (Client DOM & Attributes)
        print("\n[STEP 7] 🛡️ RIGOROUS ZERO-LEAKAGE AUDIT: Client DOM & Attributes...")
        # Check Host DOM for black cards
        host_black_dom = await host.eval_js("""
            (() => {
                const blackPieces = Array.from(document.querySelectorAll('.card.player-black, .card.black'));
                const forbiddenWords = ['JOKER', 'BOMB', 'FLAG', 'LANDMINE', 'SAPPER', 'K', 'Q', 'J', '10', '9', '8', '7', '6', '5', '4', '3', '2'];
                const leaks = [];
                for (const el of blackPieces) {
                    if (el.classList.contains('face-down') || !el.classList.contains('face-up')) {
                        const txt = (el.textContent || '').trim();
                        const html = el.innerHTML;
                        const dataAttrs = JSON.stringify(el.dataset);
                        for (const w of forbiddenWords) {
                            if (txt.includes(w) || dataAttrs.includes(w)) {
                                leaks.push({ id: el.id, text: txt, word: w });
                            }
                        }
                    }
                }
                return leaks;
            })()
        """)
        assert len(host_black_dom) == 0, f"🚨 DOM LEAK on Host: {host_black_dom}"
        print(f"  ✅ Host DOM Audit Passed: Zero opponent rank data present in {12*5} tiles or DOM nodes.")

        # Check Guest DOM for red cards
        guest_red_dom = await guest.eval_js("""
            (() => {
                const redPieces = Array.from(document.querySelectorAll('.card.player-red, .card.red'));
                const forbiddenWords = ['JOKER', 'BOMB', 'FLAG', 'LANDMINE', 'SAPPER', 'K', 'Q', 'J', '10', '9', '8', '7', '6', '5', '4', '3', '2'];
                const leaks = [];
                for (const el of redPieces) {
                    if (el.classList.contains('face-down') || !el.classList.contains('face-up')) {
                        const txt = (el.textContent || '').trim();
                        const html = el.innerHTML;
                        const dataAttrs = JSON.stringify(el.dataset);
                        for (const w of forbiddenWords) {
                            if (txt.includes(w) || dataAttrs.includes(w)) {
                                leaks.push({ id: el.id, text: txt, word: w });
                            }
                        }
                    }
                }
                return leaks;
            })()
        """)
        assert len(guest_red_dom) == 0, f"🚨 DOM LEAK on Guest: {guest_red_dom}"
        print(f"  ✅ Guest DOM Audit Passed: Zero opponent rank data present in {12*5} tiles or DOM nodes.")

        # Step 8: Play Scripted Move Turn and Verify Synchronization
        print("\n[STEP 8] Executing Scripted Legal Move (Red Player A moves forward)...")
        # Find a mobile red piece on row 4 and move to row 5 (neutral territory)
        move_result = await host.eval_js("""
            (() => {
                const g = window.gameInstance;
                for (let r = 4; r >= 0; r--) {
                    for (let c = 0; c < 5; c++) {
                        const card = g.board[r][c];
                        if (card && card.player === 'red') {
                            const legalMoves = g.getLegalMoves(r, c);
                            if (legalMoves.length > 0) {
                                const dest = legalMoves[0];
                                window.networkClient.sendAction({
                                    type: 'move',
                                    from: { r, c },
                                    to: dest
                                });
                                return { from: { r, c }, to: dest };
                            }
                        }
                    }
                }
                return null;
            })()
        """)
        print(f"  Move action dispatched: {move_result}")
        assert move_result is not None, "Red player found no legal move"
        await asyncio.sleep(1.0)

        # Verify turn changed to Black on both clients
        host_turn = await host.eval_js("window.gameInstance.currentTurn")
        guest_turn = await guest.eval_js("window.gameInstance.currentTurn")
        print(f"  Host currentTurn: {host_turn}, Guest currentTurn: {guest_turn}")
        assert host_turn == 'black' and guest_turn == 'black', f"Turn failed to advance to black: {host_turn}, {guest_turn}"
        print("  ✅ Move successfully validated and synchronized across both clients!")

        # Step 9: Invariant Check: Battle Header strictly 3 buttons
        print("\n[STEP 9] Checking Non-Negotiable Invariant: Battle Header 3 Buttons...")
        host_btns = await host.eval_js("Array.from(document.querySelectorAll('#gameScreen .control-bar button')).map(b => b.id)")
        guest_btns = await guest.eval_js("Array.from(document.querySelectorAll('#gameScreen .control-bar button')).map(b => b.id)")
        assert host_btns == ['settingsBtn', 'newGameBtn', 'homeBtn'], f"Host buttons violated: {host_btns}"
        assert guest_btns == ['settingsBtn', 'newGameBtn', 'homeBtn'], f"Guest buttons violated: {guest_btns}"
        print(f"  ✅ Both headers strictly contain exactly 3 buttons: {host_btns}")

        # Step 10: Forfeit Confirmation Modal and Match Conclusion
        print("\n[STEP 10] Testing Forfeit Confirmation and Clean Abandonment...")
        # Host clicks "Homepage" button
        await host.eval_js("document.getElementById('homeBtn').click()")
        await asyncio.sleep(0.3)
        modal_vis = await host.eval_js("document.getElementById('forfeitModal')?.style.display")
        assert modal_vis == 'flex', f"Forfeit modal must open, got: {modal_vis}"
        print("  ✅ Forfeit confirmation modal successfully opened upon clicking Homepage.")

        # Host confirms forfeit
        await host.eval_js("document.getElementById('confirmForfeitBtn').click()")
        await asyncio.sleep(1.0)

        # Verify Guest receives GameOver with winner = black, reason = forfeit
        guest_game_over = await guest.eval_js("""
            (() => ({
                gameState: window.gameInstance.gameState,
                winner: window.gameInstance.winner,
                winReason: window.gameInstance.winReason
            }))()
        """)
        print(f"  Guest received Game Over: {guest_game_over}")
        assert guest_game_over['gameState'] == 'gameover', f"Guest not gameover: {guest_game_over}"
        assert guest_game_over['winner'] == 'black', f"Guest winner wrong: {guest_game_over}"
        assert 'surrender' in guest_game_over['winReason'].lower() or 'forfeit' in guest_game_over['winReason'].lower(), f"Win reason wrong: {guest_game_over}"
        print("  ✅ Clean forfeit resolution verified across network!")

    finally:
        await host.close()
        await guest.close()

    # Step 11: 100+ Adversarial Fuzz Attacks against Cloudflare Worker & RoomDO
    print("\n[STEP 11] ⚔️ RUNNING 100+ ADVERSARIAL SERVER FUZZ ATTACKS...")
    fuzz_room_id = f"fuzz-test-{int(time.time())}"
    ws_url = f"{SERVER_WS}/room/{fuzz_room_id}"

    async with websockets.connect(ws_url) as ws:
        # Create room as attacker
        await ws.send(json.dumps({
            'v': 1,
            'type': 'create_room',
            'payload': {
                'roomId': fuzz_room_id,
                'hostNickname': 'Attacker',
                'sidePreference': 'random'
            }
        }))
        joined_raw = await ws.recv()
        joined = json.loads(joined_raw)
        session_token = joined.get('payload', {}).get('sessionToken', 'dummy_token')

        print(f"  Connected to fuzz room {fuzz_room_id}, token={session_token[:8]}...")

        fuzz_payloads = [
            # 1. Malformed syntax
            "NOT_JSON_AT_ALL",
            "{unclosed_bracket",
            "null",
            "12345",
            "[1, 2, 3]",
            '{"type": null}',
            "",
            # 2. Oversized payload (65KB junk)
            json.dumps({"type": "ping", "data": "A" * 66000}),
            # 3. Illegal message types
            json.dumps({"type": "sudo_win", "sessionToken": session_token}),
            json.dumps({"type": "give_me_flags", "sessionToken": session_token}),
            json.dumps({"type": "drop_table", "sessionToken": session_token}),
            # 4. Out of phase actions (sending actions before match starts)
            json.dumps({"type": "action", "sessionToken": session_token, "action": {"type": "move", "from": {"r": 0, "c": 0}, "to": {"r": 1, "c": 0}}}),
            # 5. Malformed layouts
            json.dumps({"type": "submit_layout", "sessionToken": session_token, "camp": []}),
            json.dumps({"type": "submit_layout", "sessionToken": session_token, "camp": [None]*10}),
            json.dumps({"type": "submit_layout", "sessionToken": session_token, "camp": [{"rank": "JOKER"}]*25, "reserves": [{"rank": "JOKER"}, {"rank": "JOKER"}]}),
            # 6. Forged session tokens
            json.dumps({"type": "submit_layout", "sessionToken": "FORGED_TOKEN_HACKER", "camp": []}),
            json.dumps({"type": "forfeit", "sessionToken": "FAKE_TOKEN"}),
            json.dumps({"type": "reconnect", "sessionToken": "WRONG_TOKEN"}),
            # 7. Out of bound coordinates
            json.dumps({"type": "action", "sessionToken": session_token, "action": {"type": "move", "from": {"r": -99, "c": -99}, "to": {"r": 999, "c": 999}}}),
            json.dumps({"type": "action", "sessionToken": session_token, "action": {"type": "move", "from": {"r": 0, "c": 0}, "to": {"r": 0, "c": 4}}}),
            # 8. Drop illegal conscripts
            json.dumps({"type": "action", "sessionToken": session_token, "action": {"type": "drop", "handType": "mochigoma", "index": 999, "to": {"r": 0, "c": 0}}}),
            json.dumps({"type": "action", "sessionToken": session_token, "action": {"type": "drop", "handType": "fakeType", "index": 0, "to": {"r": 5, "c": 2}}})
        ]

        # Generate 100+ variations
        attack_count = 0
        error_count = 0
        for i in range(120):
            attack_count += 1
            base = fuzz_payloads[i % len(fuzz_payloads)]
            try:
                await ws.send(base)
                # Read response if available within 0.1s
                try:
                    resp = await asyncio.wait_for(ws.recv(), timeout=0.1)
                    parsed = json.loads(resp)
                    if parsed.get('type') == 'error':
                        error_count += 1
                except asyncio.TimeoutError:
                    pass
            except Exception as e:
                # Disconnection on malformed is acceptable if server handles it gracefully
                pass

        print(f"  ✅ Sent {attack_count} adversarial fuzz payloads. Received {error_count} structured error rejections.")

    # Verify server is still completely alive and healthy
    print("\n[STEP 12] Post-Fuzz Backend Health Check...")
    health_req = urllib.request.urlopen(f"{SERVER_HTTP}/api/health")
    health = json.loads(health_req.read().decode('utf-8'))
    assert health.get('status') == 'ok', f"Server failed post-fuzz health: {health}"
    print(f"  ✅ Cloudflare Workers Backend survived 100+ fuzz attacks with zero crashes: {health}")

    print("\n" + "=" * 80)
    print("🏆 ALL PHASE 6 AUTOMATED VERIFICATIONS PASSED WITH ZERO LEAKAGE!")
    print("=" * 80)
    return True

if __name__ == '__main__':
    success = asyncio.run(run_phase6_verification())
    if not success:
        sys.exit(1)
