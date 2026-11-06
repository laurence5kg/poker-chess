import asyncio, json, tempfile, subprocess, urllib.request, websockets, sys

try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

async def audit_live_page():
    print("🔍 Auditing Live Deployment Artifacts via Chrome DevTools Protocol...")
    tmp_dir = tempfile.mkdtemp(prefix="chrome_audit_")
    chrome_path = r'C:\Program Files\Google\Chrome\Application\chrome.exe'
    proc = subprocess.Popen([
        chrome_path,
        '--headless=new',
        '--remote-debugging-port=9224',
        f'--user-data-dir={tmp_dir}',
        '--disable-gpu',
        '--no-sandbox',
        '--disable-extensions',
        'http://localhost:8000'
    ])
    await asyncio.sleep(2.0)

    try:
        req = urllib.request.urlopen("http://localhost:9224/json")
        pages = json.loads(req.read().decode())
        page = next((p for p in pages if p.get('type') == 'page'), None)
        if not page:
            print("❌ No matching page found!")
            return

        async with websockets.connect(page['webSocketDebuggerUrl']) as ws:
            msg_id = 1
            network_requests = []
            console_messages = []

            async def send(method, params=None):
                nonlocal msg_id
                payload = {"id": msg_id, "method": method, "params": params or {}}
                await ws.send(json.dumps(payload))
                msg_id += 1
                while True:
                    resp = json.loads(await ws.recv())
                    if resp.get('method') == 'Network.responseReceived':
                        p = resp.get('params', {})
                        r = p.get('response', {})
                        network_requests.append({
                            'url': r.get('url'),
                            'status': r.get('status'),
                            'mimeType': r.get('mimeType')
                        })
                    elif resp.get('method') == 'Console.messageAdded':
                        console_messages.append(resp.get('params', {}).get('message', {}))
                    elif resp.get('method') == 'Runtime.consoleAPICalled':
                        console_messages.append(resp.get('params', {}))
                    if resp.get('id') == payload['id']:
                        return resp.get('result', {})

            await send("Network.enable")
            await send("Console.enable")
            await send("Runtime.enable")
            await send("Page.enable")

            # Navigate and reload with cache disabled (Hard Refresh simulation)
            await send("Network.setCacheDisabled", {"cacheDisabled": True})
            await send("Page.navigate", {"url": "http://localhost:8000"})
            await asyncio.sleep(2.5)

            # Evaluate meta tags, title, favicon, audio
            eval_res = await send("Runtime.evaluate", {
                "expression": """
                (() => {
                    const ogTitle = document.querySelector('meta[property="og:title"]')?.content || null;
                    const ogDesc = document.querySelector('meta[property="og:description"]')?.content || null;
                    const ogImage = document.querySelector('meta[property="og:image"]')?.content || null;
                    const metaDesc = document.querySelector('meta[name="description"]')?.content || null;
                    const favicon = document.querySelector('link[rel="icon"]')?.href || null;
                    const title = document.title;
                    const audioAvailable = typeof window.soundFX !== 'undefined';
                    const i18nAvailable = typeof window.I18N !== 'undefined';
                    const gameAvailable = typeof window.GameEngine !== 'undefined';
                    return {
                        title,
                        metaDesc,
                        ogTitle,
                        ogDesc,
                        ogImage,
                        favicon,
                        audioAvailable,
                        i18nAvailable,
                        gameAvailable
                    };
                })()
                """,
                "returnByValue": True
            })

            data = eval_res.get('result', {}).get('value', {})
            print("\n📊 DOM & Meta Audit Results:")
            print(f"  • Page Title: '{data.get('title')}'")
            print(f"  • Meta Description: '{data.get('metaDesc')[:60]}...'")
            print(f"  • OpenGraph Title: '{data.get('ogTitle')}'")
            print(f"  • OpenGraph Image: '{data.get('ogImage')}'")
            print(f"  • Favicon Loaded: {bool(data.get('favicon'))}")
            print(f"  • Audio Engine Initialized: {data.get('audioAvailable')}")
            print(f"  • i18n Dictionary Loaded: {data.get('i18nAvailable')}")
            print(f"  • GameEngine Loaded: {data.get('gameAvailable')}")

            print("\n🌐 Network Requests Audit (Status Codes):")
            failed_requests = [r for r in network_requests if r['status'] >= 400]
            for r in network_requests:
                short_url = r['url'].split('/')[-1] or r['url']
                print(f"  [{r['status']}] {short_url} ({r['mimeType']})")

            print(f"\nTotal Network Requests: {len(network_requests)} | Failed/404 Requests: {len(failed_requests)}")
            print(f"Console Errors/Warnings Logged: {len(console_messages)}")

            if len(failed_requests) == 0 and len(console_messages) == 0:
                print("\n✅ ZERO 404s, ZERO CONSOLE ERRORS, 100% CLEAN DEPLOYMENT ARTIFACTS!")
            else:
                print(f"\n⚠️ Issues: Failed={failed_requests}, Console={console_messages}")

    finally:
        proc.terminate()

if __name__ == '__main__':
    asyncio.run(audit_live_page())
