import json, base64, io, numpy as np
from PIL import Image
t = open('/mnt/user-data/outputs/MCON_Sandbox.html').read()
i = t.index('const PRIUS_LP = ') + len('const PRIUS_LP = '); j = t.index(';\n', i); CUR = json.loads(t[i:j])
NEW = json.load(open('/tmp/lp/prius_lp3.json')); lo = np.array(CUR['lo']); hi = np.array(CUR['hi'])
dec = lambda s, ty: np.frombuffer(base64.b64decode(s), ty); enc = lambda a: base64.b64encode(np.ascontiguousarray(a).tobytes()).decode()
shell = [p for p in NEW['parts'] if p['key'] == 'lp_shell'][0]
q = dec(shell['p'], np.int16).reshape(-1, 3).astype(float); P = lo + (q + 32768) / 65535 * (hi - lo)
UV = dec(shell['uv'], np.float32).reshape(-1, 2); N = dec(shell['nm'], np.int8).reshape(-1, 3) / 127
IX = dec(shell['ix'], np.uint32 if shell['i32'] else np.uint16).reshape(-1, 3).astype(np.int64)
NSHELL = 1495   # the faces before the mirror panels
def mk(key, tex, faces):
    used = np.unique(faces); rm = -np.ones(len(P), np.int64); rm[used] = np.arange(len(used))
    qp = np.clip(np.round((P[used] - lo) / (hi - lo) * 65535 - 32768), -32768, 32767).astype(np.int16)
    return {'key': key, 'tex': tex, 'color': None, 'n': int(len(used)), 'i32': 0, 'p': enc(qp), 'nm': enc(np.round(N[used] * 127).astype(np.int8)), 'uv': enc(UV[used].astype(np.float32)), 'ix': enc(rm[faces].astype(np.uint16))}
S = np.load('/tmp/lp/sheet2.npy'); HM = np.load('/tmp/lp/head_mask.npy'); TM = np.load('/tmp/lp/tail_mask.npy')
def png(arr, size=(256, 512), colours=64, nearest=False):
    im = Image.fromarray(arr.astype(np.uint8)); im = im.resize(size, Image.NEAREST if nearest else Image.BOX)
    a = np.array(im); rgb = Image.fromarray(a[:, :, :3]).quantize(colors=colours, method=Image.MEDIANCUT, dither=Image.NONE).convert('RGB')
    out = Image.fromarray(np.dstack([np.array(rgb), a[:, :, 3]])) if a.shape[2] == 4 else rgb
    b = io.BytesIO(); out.save(b, 'PNG', optimize=True); return 'data:image/png;base64,' + base64.b64encode(b.getvalue()).decode()
# which shell faces touch the lamps (sampled at corners, edge midpoints and centre)
def touches(mask, f):
    uv = UV[IX[f]]; pts = list(uv) + [uv.mean(0)] + [(uv[a] + uv[b]) / 2 for a, b in ((0, 1), (1, 2), (2, 0))]
    for u, v in pts:
        x = int(np.clip(u * 512, 0, 511)); y = int(np.clip((1 - v) * 1024, 0, 1023))
        if mask[max(0, y - 1):y + 2, max(0, x - 1):x + 2].any(): return True
    return False
headF = [f for f in range(NSHELL) if touches(HM, f)]; tailF = [f for f in range(NSHELL) if touches(TM, f)]
glowH = np.zeros_like(S); glowH[HM] = S[HM]; glowH[:, :, 3] = 255
glowT = np.zeros_like(S); glowT[TM] = S[TM]; glowT[:, :, 3] = 255
alpha = np.repeat(S[:, :, 3:4], 3, axis=2); alpha = np.dstack([alpha, np.full(S.shape[:2], 255)])
parts = [shell, mk('lp_inner', 'lp_alpha', IX[:NSHELL]), mk('lp_head', 'lp_head', IX[headF]), mk('lp_tail', 'lp_tail', IX[tailF])]
KEEP = ['priuswheel2.tga', 'color:prmirror', 'priusvolan.tga', 'priusint5.tga', 'priusint1.tga', 'prius_int4.tga', 'priusint3.tga', 'priusint2.tga']
parts += [p for p in CUR['parts'] if p['key'] in KEEP]
tex = {k: v for k, v in CUR['tex'].items() if k in {p['tex'] for p in parts}}
tex['lp_shell'] = NEW['tex']['lp_shell']
tex['lp_alpha'] = {'uri': png(alpha, colours=8), 'alpha': 0, 'ps1': 1}
tex['lp_head'] = {'uri': png(glowH, colours=32), 'alpha': 0, 'ps1': 1}
tex['lp_tail'] = {'uri': png(glowT, colours=32), 'alpha': 0, 'ps1': 1}
OUT = {'lo': CUR['lo'], 'hi': CUR['hi'], 'parts': parts, 'tex': tex}
t = t[:i] + json.dumps(OUT, separators=(',', ':')) + t[j:]
old = "if (P.key === 'lp_shell') { paintM.map = mp; paintM.transparent = true; paintM.side = THREE.FrontSide; paintM.needsUpdate = true;"
assert t.count(old) == 1
t = t.replace(old, "if (P.key === 'lp_shell') { paintM.map = mp; paintM.transparent = true; paintM.alphaTest = 0.1; paintM.side = THREE.FrontSide; paintM.needsUpdate = true;")
a = t.index('// the PS1 version of the Prius, built the way PS1 cars were:'); b = t.index('\n', t.index('// real mirror housings', a))
t = t[:a] + "// the PS1 version of the Prius: the real outside shrunk to ~1,500 triangles (the same gentle method as the interior), with\n// everything (lights, grille, trim, windows, plate, badges) baked into one 256 x 512 texture from straight-on views of the\n// real car; flat crossed cut-out mirrors; a dark inner lining; lamp glow layers; simple wheels; the original interior." + t[b:]
open('/mnt/user-data/outputs/MCON_Sandbox.html', 'w').write(t)
tris = {p['key']: len(base64.b64decode(p['ix'])) // (12 if p['i32'] else 6) for p in parts}
print(tris); print('outside', sum(v for k, v in tris.items() if k in ('lp_shell', 'priuswheel2.tga')), '| file', round(len(t) / 1e6, 2), 'MB')
