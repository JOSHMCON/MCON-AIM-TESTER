import json, base64, io, numpy as np
from PIL import Image
D = json.load(open('/tmp/lp/prius.json')); OLD = json.load(open('/tmp/lp/prius_lp.json')); lo = np.array(D['lo']); hi = np.array(D['hi'])
enc = lambda a: base64.b64encode(np.ascontiguousarray(a).tobytes()).decode()
E = np.load('/tmp/lp/ext3.npz'); P, UV, IX = E['P'], E['UV'], E['IX']
nshell = 1495
# smooth normals across the shell (corners at the same spot share a normal); the mirror panels stay flat
fn = np.cross(P[IX[:, 1]] - P[IX[:, 0]], P[IX[:, 2]] - P[IX[:, 0]]); N = np.zeros_like(P)
key = np.round(P / 1e-4).astype(np.int64); _, grp = np.unique(key, axis=0, return_inverse=True); grp = grp.ravel()
acc = np.zeros((grp.max() + 1, 3))
for c in range(3): np.add.at(acc, grp[IX[:nshell, c]], fn[:nshell])
for c in range(3): N[IX[:nshell, c]] = acc[grp[IX[:nshell, c]]]
for f in range(nshell, len(IX)): N[IX[f]] = fn[f]
N /= np.maximum(np.linalg.norm(N, axis=1, keepdims=True), 1e-12)
def mk(key, tex, P, UV, IX, N):
    used = np.unique(IX); rm = -np.ones(len(P), np.int64); rm[used] = np.arange(len(used)); p = P[used]
    qp = np.clip(np.round((p - lo) / (hi - lo) * 65535 - 32768), -32768, 32767).astype(np.int16)
    return {'key': key, 'tex': tex, 'color': None, 'n': int(len(p)), 'i32': int(len(p) >= 65536), 'p': enc(qp), 'nm': enc(np.round(N[used] * 127).astype(np.int8)), 'uv': enc(UV[used].astype(np.float32)), 'ix': enc(rm[IX].astype(np.uint32 if len(p) >= 65536 else np.uint16))}
wh = np.load('/tmp/lp/wheels.npz'); WP, WUV, WIX = wh['P'], wh['UV'], wh['IX']
wfn = np.cross(WP[WIX[:, 1]] - WP[WIX[:, 0]], WP[WIX[:, 2]] - WP[WIX[:, 0]]); WN = np.zeros_like(WP)
for c in range(3): np.add.at(WN, WIX[:, c], wfn)
WN /= np.maximum(np.linalg.norm(WN, axis=1, keepdims=True), 1e-12)
parts = [mk('lp_shell', 'lp_shell', P, UV, IX, N), mk('priuswheel2.tga', 'priuswheel2.tga', WP, WUV, WIX, WN)]
KEEP = ['priusvolan.tga', 'priusint5.tga', 'color:prmirror', 'priusint1.tga', 'prius_int4.tga', 'priusint3.tga', 'priusint2.tga']
parts += [p for p in OLD['parts'] if p['key'] in KEEP]
tex = {k: v for k, v in OLD['tex'].items() if k in {p['tex'] for p in parts}}
S = np.load('/tmp/lp/sheet2.npy')
small = np.array(Image.fromarray(S.astype(np.uint8), 'RGBA').resize((256, 512), Image.BOX)).astype(float)
a = small[:, :, 3]; small[:, :, 3] = np.where(a < 60, 0, np.where(a > 245, 255, np.round(a / 255 * 4) / 4 * 255))   # cut-outs hard, glass in steps
rgb = np.array(Image.fromarray(small[:, :, :3].astype(np.uint8)).quantize(colors=64, method=Image.MEDIANCUT, dither=Image.NONE).convert('RGB'))
b = io.BytesIO(); Image.fromarray(np.dstack([rgb, small[:, :, 3].astype(np.uint8)])).save(b, 'PNG', optimize=True)
tex['lp_shell'] = {'uri': 'data:image/png;base64,' + base64.b64encode(b.getvalue()).decode(), 'alpha': 1, 'ps1': 1}
wb = io.BytesIO(); Image.open('/tmp/lp/wheel_atlas.png').convert('RGB').quantize(colors=32, method=Image.MEDIANCUT, dither=Image.NONE).convert('RGB').save(wb, 'PNG', optimize=True)
tex['priuswheel2.tga'] = {'uri': 'data:image/png;base64,' + base64.b64encode(wb.getvalue()).decode(), 'alpha': 0, 'ps1': 1}
out = {'lo': D['lo'], 'hi': D['hi'], 'parts': parts, 'tex': tex}
json.dump(out, open('/tmp/lp/prius_lp3.json', 'w'), separators=(',', ':'))
tris = {p['key']: len(base64.b64decode(p['ix'])) // (12 if p['i32'] else 6) for p in parts}
print(tris); print('outside', tris['lp_shell'] + tris['priuswheel2.tga'], '| total', sum(tris.values()), '| data', round(len(json.dumps(out, separators=(",", ":"))) / 1e6, 2), 'MB')
