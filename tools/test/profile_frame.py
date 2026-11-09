import asyncio, json
from playwright.async_api import async_playwright
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(args=['--use-gl=swiftshader','--enable-webgl','--ignore-gpu-blocklist'])
        pg = await b.new_page(viewport={'width': 1100, 'height': 620})
        errs = []
        pg.on('pageerror', lambda e: errs.append(str(e)[:300]))
        await pg.add_init_script("navigator.getGamepads = () => []; localStorage.clear();")
        await pg.goto('file:///tmp/prof.html'); await pg.wait_for_timeout(500)
        await pg.click('#playBtn'); await pg.wait_for_timeout(15000)
        await pg.click('#expandBtn'); await pg.wait_for_timeout(2000)
        r = await pg.evaluate("window.__prof()")
        for ps in r.pop('passes'): print(ps)
        print(json.dumps(r))
        print('errors:', errs[:3])
        await b.close()
asyncio.run(main())
