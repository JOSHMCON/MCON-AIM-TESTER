import json, base64, io, numpy as np, trimesh
from PIL import Image
exec(open('/tmp/lp/hull.py').read().split("EXT = [")[0])
d = np.load('/tmp/lp/ext_pre.npz'); SP, SIX = d['P'], d['IX']
boxes = np.load('/tmp/lp/ext1.npz', allow_pickle=True)['boxes'] if False else None
TEX = {t: np.array(Image.open(io.BytesIO(base64.b64decode(v['uri'].split(',', 1)[1]))).convert('RGBA')) for t, v in D['tex'].items()}
EXT = ['prius_body.tga', 'prius_doorhandle.tga', 'priusparts1.tga', 'priusglass1.tga', 'prius1.tga', 'prius2.tga', 'priuslogo2.tga']
def mesh_of(texs):
    V, F, FP, FUV = [], [], [], []; off = 0
    for k, P in enumerate(D['parts']):
        if P['tex'] not in texs and P['key'] not in texs: continue
        pos, uv, ix = part(P); V.append(pos); F.append(ix + off); FP += [k] * len(ix); FUV.append(uv[ix]); off += len(pos)
    m = trimesh.Trimesh(np.vstack(V), np.vstack(F), process=False); return m, np.array(FP), np.vstack(FUV), trimesh.ray.ray_pyembree.RayMeshIntersector(m)
ext, FP, FUV, inter = mesh_of(EXT)
PAINT = [236, 236, 236]
def colour(mesh, FP, FUV, pts, tri):
    out = np.zeros((len(pts), 4)); bary = trimesh.triangles.points_to_barycentric(mesh.triangles[tri], pts); uv = (FUV[tri] * bary[:, :, None]).sum(1)
    for k in np.unique(FP[tri]):
        m = FP[tri] == k; P = D['parts'][k]; t = P['tex']
        if t in ('prius_body.tga', 'prius_doorhandle.tga'): out[m] = [*PAINT, 255]; continue
        if t is None or t not in TEX: out[m] = [22, 24, 28, 255]; continue   # (the mirror glass: dark)
        im = TEX[t]; H, W = im.shape[:2]; u = uv[m]
        c = im[np.clip(((1 - u[:, 1] % 1) * H).astype(int), 0, H - 1), np.clip(((u[:, 0] % 1) * W).astype(int), 0, W - 1)].astype(float)
        if t == 'priusglass1.tga':
            clear = c[:, 3] < 150; c[clear, :3] = c[clear, :3] * 0.25 + np.array([26, 33, 40]) * 0.75; c[:, 3] = np.maximum(c[:, 3], 140)
        elif D['tex'][t]['alpha']: see = c[:, 3] < 128; c[see] = [*PAINT, 255]; c[:, 3] = 255
        else: c[:, 3] = 255
        out[m] = c
    return out
# ---- the views (a PS1 car texture: left, right, top, front, rear), 100 px per metre, on a 512 x 1024 sheet
PPM = 100.0
VIEWS = {   # name: (axis, sign of the view direction's facing, sheet rectangle x0, y0, w, h, how 3D maps to (a, b) on it)
  'left':  ('x', -1, 0, 0, 512, 160), 'right': ('x', 1, 0, 160, 512, 160), 'top': ('y', 1, 0, 320, 512, 200),
  'front': ('z', -1, 0, 520, 220, 170), 'rear': ('z', 1, 240, 520, 220, 170)}
Z0, Z1, X0, X1, Y0, Y1 = -2.56, 2.56, -1.12, 1.12, 0.12, 1.80
def ab(view, p):   # 3D point -> (a, b) in the view's own metres (a across, b up the sheet)
    if view == 'left':  return (p[..., 2] - Z0), (Y1 - p[..., 1])
    if view == 'right': return (Z1 - p[..., 2]), (Y1 - p[..., 1])
    if view == 'top':   return (p[..., 2] - Z0), (p[..., 0] - X0)
    if view == 'front': return (p[..., 0] - X0), (Y1 - p[..., 1])
    if view == 'rear':  return (X1 - p[..., 0]), (Y1 - p[..., 1])
def sheet_uv(view, p):
    a, b = ab(view, p); ax, s, x0, y0, w, h = VIEWS[view]
    return np.stack([(x0 + a * PPM) / 512.0, 1 - (y0 + b * PPM) / 1024.0], -1)
# ---- assign every face of the simplified shell to the view it faces most
fn = np.cross(SP[SIX[:, 1]] - SP[SIX[:, 0]], SP[SIX[:, 2]] - SP[SIX[:, 0]]); fn /= np.maximum(np.linalg.norm(fn, axis=1, keepdims=True), 1e-12)
# make normals point outward (away from the car's middle line)
cen = SP[SIX].mean(1); out = cen - np.c_[np.zeros(len(cen)), np.full(len(cen), 0.8), np.clip(cen[:, 2], -1.6, 1.6)]
flip = (fn * out).sum(1) < 0; SIX[flip] = SIX[flip][:, [0, 2, 1]]; fn[flip] *= -1
under = fn[:, 1] < -0.6
choice = np.where(under, 'under', np.where(np.abs(fn[:, 1]) >= np.maximum(np.abs(fn[:, 0]), np.abs(fn[:, 2])), 'top',
          np.where(np.abs(fn[:, 0]) >= np.abs(fn[:, 2]), np.where(fn[:, 0] < 0, 'left', 'right'), np.where(fn[:, 2] < 0, 'front', 'rear'))))
for v in ['left', 'right', 'top', 'front', 'rear', 'under']: print(f'{v:6s} faces: {(choice == v).sum()}')
P, UV, IX = [], [], []
for f in range(len(SIX)):
    v = choice[f]; ids = []
    for vi in SIX[f]:
        p = SP[vi]; uv = sheet_uv(v, p) if v != 'under' else np.array([500 / 512, 1 - 1010 / 1024])
        P.append(p); UV.append(uv); ids.append(len(P) - 1)
    IX.append(ids)
P = np.array(P); UV = np.array(UV); IX = np.array(IX)
# ---- photograph the real car from each side, straight on
S = np.zeros((1024, 512, 4)); S[:, :, 3] = 0
for v, (axis, sgn, x0, y0, w, h) in VIEWS.items():
    yy, xx = np.mgrid[y0:y0 + h, x0:x0 + w]; a = (xx + 0.5 - x0) / PPM; b = (yy + 0.5 - y0) / PPM
    if v == 'left':  org = np.c_[np.full(a.size, -4), Y1 - b.ravel(), Z0 + a.ravel()]; dr = [1, 0, 0]
    if v == 'right': org = np.c_[np.full(a.size, 4), Y1 - b.ravel(), Z1 - a.ravel()]; dr = [-1, 0, 0]
    if v == 'top':   org = np.c_[X0 + b.ravel(), np.full(a.size, 4), Z0 + a.ravel()]; dr = [0, -1, 0]
    if v == 'front': org = np.c_[X0 + a.ravel(), Y1 - b.ravel(), np.full(a.size, -5)]; dr = [0, 0, 1]
    if v == 'rear':  org = np.c_[X1 - a.ravel(), Y1 - b.ravel(), np.full(a.size, 5)]; dr = [0, 0, -1]
    locs, ri, ti = inter.intersects_location(org.astype(float), np.tile(dr, (len(org), 1)).astype(float), multiple_hits=False)
    col = np.zeros((len(org), 4)); col[:, :3] = PAINT; col[:, 3] = 255
    if len(ri): col[ri] = colour(ext, FP, FUV, locs, ti)
    S[y0:y0 + h, x0:x0 + w] = col.reshape(h, w, 4)
S[1000:1024, 488:512] = [18, 19, 22, 255]   # the underside
np.save('/tmp/lp/sheet.npy', S); np.savez('/tmp/lp/ext2.npz', P=P, UV=UV, IX=IX)
Image.fromarray(S.astype(np.uint8)).save('/tmp/lp/sheet.png'); print('shell', len(IX), 'triangles')
