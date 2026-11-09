import asyncio, math
from playwright.async_api import async_playwright
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(args=['--use-gl=swiftshader','--enable-webgl','--ignore-gpu-blocklist'])
        pg = await b.new_page(viewport={'width': 1000, 'height': 560})
        errs = []
        pg.on('pageerror', lambda e: errs.append(str(e)[:300]))
        await pg.add_init_script("navigator.getGamepads = () => []; localStorage.clear();")
        await pg.goto('file:///tmp/tree.html'); await pg.wait_for_timeout(500)
        await pg.click('#playBtn'); await pg.wait_for_timeout(15000)
        await pg.click('#expandBtn'); await pg.wait_for_timeout(1500)
        print(await pg.evaluate("window.__bbTree && window.__bbTree.cards"), 'cards')
        await pg.screenshot(path='/tmp/t_spawn.png')
        tx, tz = -5.2, -1.5
        for name, dx, dz, pitch in [('near', 2.5, 6.5, 0.32), ('side', -7.0, 3.0, 0.3)]:
            x, z = tx + dx, tz + dz; yaw = math.atan2(-(tx - x), -(tz - z))
            await pg.evaluate(f"window.__look({x}, {z}, {yaw}, {pitch})"); await pg.wait_for_timeout(2000)
            await pg.screenshot(path=f'/tmp/t_{name}.png')
        print('errors:', errs[:3])
        await b.close()
asyncio.run(main())
