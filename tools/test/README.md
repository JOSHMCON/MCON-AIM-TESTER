# Browser testing

1. `pip install playwright && python3 -m playwright install chromium`
2. Get three.js r128 locally (`npm i three@0.128.0` → `node_modules/three/build/three.min.js`).
3. `python3 make_test_copy.py ../../index.html /abs/path/three.min.js` → `test.html` with hooks:
   `__move(x,z)` (move the car), `__veh('prius'|'truck')`, `__look(x,z,yaw,pitch)`, `__look2(x,y,z,yaw,pitch)`.
4. Launch Chromium with `--use-gl=swiftshader --enable-webgl --ignore-gpu-blocklist`, open test.html,
   stub `navigator.getGamepads = () => []`, clear localStorage, click `#playBtn`, wait ~15 s, click `#expandBtn`.
5. Collect `pageerror` and console errors; take screenshots; LOOK at them.

The scripts here (`screens_prius.py`, `screens_tree.py`, `profile_frame.py`) are the ones used in the session;
they point at `/tmp/...` test copies — update the paths. `profile_frame.py` needs a `window.__prof()` hook that
wraps `renderer.render` to log draw calls/triangles per render target (see HANDOFF for the numbers).
To test a TUNE setting (e.g. the OG Prius), set localStorage `mcon-truck-tune` to `{"priusHD": true}` before load.
