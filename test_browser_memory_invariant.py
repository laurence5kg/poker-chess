import asyncio
import json
import os
import shutil
import subprocess
import sys
import tempfile
import urllib.request
import websockets

sys.stdout.reconfigure(encoding='utf-8')

async def run():
    print("🧠 Testing Browser High AI Card Memory Invariant via CDP...")
    tmp_dir = tempfile.mkdtemp(prefix="chrome_mem_test_")
    chrome_path = r'C:\Program Files\Google\Chrome\Application\chrome.exe'
    proc = subprocess.Popen([
        chrome_path,
        '--headless=new',
        '--remote-debugging-port=9223',
        f'--user-data-dir={tmp_dir}',
        '--disable-gpu',
        '--no-sandbox',
        '--disable-extensions',
        'http://localhost:8000'
    ])
    await asyncio.sleep(2.0)

    try:
        req = urllib.request.urlopen("http://localhost:9223/json")
        pages = json.loads(req.read().decode())
        page = next((p for p in pages if p.get('type') == 'page'), None)
        if not page:
            print("❌ No matching tab found!")
            return

        async with websockets.connect(page['webSocketDebuggerUrl']) as ws:
            msg_id = 1

            async def send(method, params=None):
                nonlocal msg_id
                payload = {"id": msg_id, "method": method, "params": params or {}}
                await ws.send(json.dumps(payload))
                msg_id += 1
                while True:
                    resp = json.loads(await ws.recv())
                    if resp.get('id') == payload['id']:
                        return resp.get('result', {})

            await send("Page.enable")
            await send("Runtime.enable")
            await send("Page.navigate", {"url": "http://localhost:8000"})
            await asyncio.sleep(2.5)

            # Evaluate in page: Setup scenario where High AI knows human card is 10,
            # and AI card 6 is adjacent to it. Verify AI refuses to suicide into the 10!
            eval_script = """
            (() => {
                const engine = window.gameInstance;
                if (!engine) return { error: "No gameInstance found", hasGameEngine: typeof window.GameEngine };

                engine.resetForNewGame({ mode: 'pve', aiLevel: 'high', humanSide: 'red' });
                engine.startBattle();
                engine.currentTurn = 'black';

                for (let r = 0; r < 12; r++) {
                    for (let c = 0; c < 5; c++) {
                        engine.board[r][c] = null;
                    }
                }

                // Put human's 10 at (5, 2)
                const humanCard = {
                    id: 9991,
                    player: 'red',
                    rank: '10',
                    suit: '♠',
                    faceUp: false,
                    isFlag: false,
                    isBomb: false,
                    isLandmine: false,
                    isSapper: false,
                    isMochigoma: false
                };
                engine.board[5][2] = humanCard;

                // Register human card in Black AI memory as rank 10
                engine.aiMemory['black'].set(humanCard, {
                    player: 'red',
                    rank: '10',
                    rankVal: 10,
                    isBomb: false,
                    isLandmine: false,
                    isFlag: false,
                    isSapper: false,
                    isMochigoma: false
                });

                // Put Black AI's 6 at (6, 2) adjacent to human's 10
                const botCard6 = {
                    id: 9992,
                    player: 'black',
                    rank: '6',
                    suit: '♥',
                    faceUp: false,
                    isFlag: false,
                    isBomb: false,
                    isLandmine: false,
                    isSapper: false,
                    isMochigoma: false
                };
                engine.board[6][2] = botCard6;

                // Also put a known Landmine at (5, 4) and a Sapper at (6, 4)
                const humanMine = {
                    id: 9993,
                    player: 'red',
                    rank: 'Q',
                    suit: '♦',
                    faceUp: false,
                    isFlag: false,
                    isBomb: false,
                    isLandmine: true,
                    isSapper: false,
                    isMochigoma: false
                };
                engine.board[5][4] = humanMine;
                engine.aiMemory['black'].set(humanMine, {
                    player: 'red',
                    rank: 'Q',
                    rankVal: 0,
                    isBomb: false,
                    isLandmine: true,
                    isFlag: false,
                    isSapper: false,
                    isMochigoma: false
                });

                const botSapper = {
                    id: 9994,
                    player: 'black',
                    rank: 'A',
                    suit: '♠',
                    faceUp: false,
                    isFlag: false,
                    isBomb: false,
                    isLandmine: false,
                    isSapper: true,
                    isMochigoma: false
                };
                engine.board[6][4] = botSapper;

                const actions = engine.getAllLegalActions('black');
                const chosen = engine.getBestActionHigh(actions, 'black', 'red');

                const attackedKnown10 = (chosen.type === 'move' && chosen.to.r === 5 && chosen.to.c === 2);
                const suicideMove = actions.find(a => a.type === 'move' && a.to.r === 5 && a.to.c === 2);
                const sapperDisarmMove = actions.find(a => a.type === 'move' && a.from.r === 6 && a.from.c === 4 && a.to.r === 5 && a.to.c === 4);

                return {
                    totalActions: actions.length,
                    chosenAction: { type: chosen.type, from: chosen.from, to: chosen.to, score: chosen.score },
                    attackedKnown10: attackedKnown10,
                    suicideMoveScore: suicideMove ? suicideMove.score : null,
                    sapperDisarmScore: sapperDisarmMove ? sapperDisarmMove.score : null,
                    testPassed: !attackedKnown10 && suicideMove && suicideMove.score === -9999999 && sapperDisarmMove && sapperDisarmMove.score >= 160000
                };
            })()
            """

            res = await send("Runtime.evaluate", {"expression": eval_script, "returnByValue": True})
            print(f"Full CDP response: {json.dumps(res, indent=2)}")
            val = res.get('result', {}).get('value', {})
            print(f"Test Result: {json.dumps(val, indent=2)}")

            if val.get('testPassed'):
                print("✅ ABSOLUTE BLUNDER VETO VERIFIED: High AI NEVER attacks known higher enemy card! Score = -9999999")
            else:
                print("❌ Test failed!")

    finally:
        proc.terminate()
        try:
            proc.wait(timeout=3)
        except Exception:
            proc.kill()
        shutil.rmtree(tmp_dir, ignore_errors=True)

if __name__ == '__main__':
    asyncio.run(run())
