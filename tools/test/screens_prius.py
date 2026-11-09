import asyncio, math
from playwright.async_api import async_playwright
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(args=['--use-gl=swiftshader','--enable-webgl','--ignore-gpu-blocklist'])
        pg = await b.new_page(viewport={'width': 1000, 'height': 560})
        errs = []
        pg.on('pageerror', lambda e: errs.append(str(e)[:300]))
        pg.on('console', lambda m: errs.append(m.text[:300]) if m.type == 'error' and 'net::' not in m.text else None)
        await pg.add_init_script("navigator.getGamepads = () => []; localStorage.clear();")
        await pg.goto('file:///tmp/lpg.html'); await pg.wait_for_timeout(500)
        await pg.click('#playBtn'); await pg.wait_for_timeout(16000)
        await pg.click('#expandBtn'); await pg.wait_for_timeout(800)
        await pg.evaluate("window.__veh('prius')"); await pg.evaluate("window.__move(9, 2)"); await pg.wait_for_timeout(4000)
        x, y, z, v, nk = await pg.evaluate("window.__veh('prius')")
        print('vehicle', v, 'at', round(x, 1), round(z, 1), '| Prius triangles in game', await pg.evaluate("window.__tris()"))
        for name, dx, dz, h in [('rear', -2.6, 3.8, 0.5), ('front', 2.4, -3.8, 0.4), ('side', 5.5, 0.4, 0.2)]:
            px, pz = x + dx, z + dz; yaw = math.atan2(-(x - px), -(z - pz)); pitch = -math.atan2(h + 1.6 - 0.7, math.hypot(dx, dz))
            await pg.evaluate(f"window.__look2({px}, {y + h + 1.6}, {pz}, {yaw}, {pitch})"); await pg.wait_for_timeout(1800)
            await pg.screenshot(path=f'/tmp/lpg_{name}.png')
        await pg.evaluate(f"window.__look2({x + 1.6}, {y + 1.7}, {z + 0.5}, 0, 0)"); await pg.wait_for_timeout(800)
        await pg.keyboard.down('KeyR'); await pg.wait_for_timeout(400); await pg.keyboard.up('KeyR'); await pg.wait_for_timeout(4000)
        await pg.screenshot(path='/tmp/lpg_inside.png')
        print('errors:', errs[:3])
        await b.close()
asyncio.run(main())
