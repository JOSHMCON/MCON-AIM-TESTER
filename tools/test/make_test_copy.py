# Make test.html from index.html: local three.js (no network in many sandboxes) + debug hooks.
# Usage: python3 make_test_copy.py index.html /path/to/three.min.js(r128)
import sys
src, three = sys.argv[1], sys.argv[2]
t = open(src).read().replace('https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js', 'file://' + three)
hooks = """    window.__move = (x, z) => { const y = heightAt(x, z) + 1.2; K.S.p[0] = x; K.S.p[1] = y; K.S.p[2] = z; return [x, y, z]; };
    window.__veh = v => { setVehicle(v); return [K.g.position.x, K.g.position.y, K.g.position.z, VEH]; };
    window.__look = (x, z, yaw, pitch) => { s.px = x; s.pz = z; s.yaw = yaw; s.pitch = pitch || 0; };
    window.__look2 = (x, y, z, yaw, pitch) => { s.px = x; s.pz = z; s.py = y; s.vy = 0; s.yaw = yaw; s.pitch = pitch; };
"""
anchor = "    function placeTreeAt(tr, x, z) {"
assert t.count(anchor) == 1, 'anchor moved: put the hooks inside the game module, before any function there'
t = t.replace(anchor, hooks + anchor, 1)
open('test.html', 'w').write(t); print('wrote test.html')
