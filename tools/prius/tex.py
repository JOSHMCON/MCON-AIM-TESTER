import json, base64, io, numpy as np
from PIL import Image
L = json.load(open('/tmp/lp/prius_lp_geo.json'))
SIZE = {'priusvolan.tga': 64, 'priuswheel2.tga': 64, 'Brakes.tga': 32, 'priusint5.tga': 64, 'priuslogo2.tga': 128, 'priuslogo1.tga': 64, 'priusglass1.tga': 128,
        'priusparts1.tga': 128, 'priusint1.tga': 64, 'priusint3.tga': 64, 'priusint2.tga': 64, 'prius2.tga': 128, 'prius1.tga': 128, 'prius_doorhandle.tga': 32, 'prius_rim.tga': 128, 'prius_body.tga': 32}
for name, T in L['tex'].items():
    if name not in SIZE: continue
    raw = base64.b64decode(T['uri'].split(',', 1)[1]); s = SIZE[name]
    im = Image.open(io.BytesIO(raw)).convert('RGBA').resize((s, s), Image.LANCZOS); a = np.array(im)
    rgb = np.array(im.convert('RGB').quantize(colors=32, method=Image.MEDIANCUT, dither=Image.NONE).convert('RGB'))   # a 32-colour palette, like a PS1 CLUT
    if name == 'priusglass1.tga': clear = a[:, :, 3] < 150; rgb[clear] = (rgb[clear] * 0.25 + np.array([26, 33, 40]) * 0.75).astype(np.uint8)   # the clear parts become dark tinted glass
    if name == 'priusglass1.tga': al = np.maximum((np.round(a[:, :, 3] / 255 * 4) / 4 * 255), 115).astype(np.uint8)   # PS1-dark tinted glass (still see-through from inside), in a few steps
    elif T['alpha']: al = np.where(a[:, :, 3] > 110, 255, 0).astype(np.uint8)                       # badges and rims: hard cut-outs
    else: al = None
    out = Image.fromarray(np.dstack([rgb, al])) if al is not None else Image.fromarray(rgb)
    buf = io.BytesIO(); out.save(buf, 'PNG', optimize=True)
    T['uri'] = 'data:image/png;base64,' + base64.b64encode(buf.getvalue()).decode(); T['ps1'] = 1
json.dump(L, open('/tmp/lp/prius_lp.json', 'w'), separators=(',', ':'))
print('packed', round(len(json.dumps(L, separators=(",", ":"))) / 1e6, 2), 'MB')
