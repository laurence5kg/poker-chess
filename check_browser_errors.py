import asyncio
import json
import shutil
import subprocess
import sys
import tempfile
import urllib.request
import websockets

sys.stdout.reconfigure(encoding='utf-8')

async def check_errors():
    tmp_dir = tempfile.mkdtemp(prefix="chrome_err_")
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
                    if resp.get('method') == 'Runtime.exceptionThrown':
                        print("🔥 EXCEPTION THROWN:", json.dumps(resp['params'], indent=2))
                    elif resp.get('method') == 'Console.messageAdded':
                        print("📢 CONSOLE MSG:", resp['params']['message']['text'])
                    if resp.get('id') == msg_id:
                        return resp.get('result', {})

            await send('Page.enable')
            await send('Runtime.enable')
            await send('Console.enable')

            print("Navigating to http://localhost:8000 ...")
            await send('Page.navigate', {'url': 'http://localhost:8000'})
            await asyncio.sleep(2)

            # Read any buffered messages
            while True:
                try:
                    raw = await asyncio.wait_for(ws.recv(), timeout=1.0)
                    resp = json.loads(raw)
                    if resp.get('method') == 'Runtime.exceptionThrown':
                        print("🔥 EXCEPTION THROWN:", json.dumps(resp['params'], indent=2))
                    elif resp.get('method') == 'Console.messageAdded':
                        print("📢 CONSOLE MSG:", resp['params']['message']['text'])
                except asyncio.TimeoutError:
                    break

    finally:
        proc.terminate()
        try: shutil.rmtree(tmp_dir, ignore_errors=True)
        except: pass

asyncio.run(check_errors())
