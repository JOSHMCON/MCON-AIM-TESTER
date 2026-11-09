import json, base64, io, numpy as np, trimesh
from PIL import Image
D = json.load(open('/tmp/lp/prius.json')); lo = np.array(D['lo']); hi = np.array(D['hi'])
dec = (lambda s, t: np.frombuffer(base64.b64decode(s), t))
def part(P):
    q = dec(P['p'], np.int16).reshape(-1, 3).astype(np.float64); pos = lo + (q + 32768) / 65535 * (hi - lo)
    return pos, dec(P['uv'], np.float32).reshape(-1, 2).astype(np.float64), dec(P['ix'], np.uint32 if P['i32'] else np.uint16).reshape(-1, 3).astype(np.int64)
EXT = ['prius_body.tga', 'prius_doorhandle.tga', 'priusparts1.tga', 'priusglass1.tga', 'prius1.tga', 'prius2.tga', 'priuslogo2.tga']
V, F, FP, FUV = [], [], [], []
off = 0
for k, P in enumerate(D['parts']):
    if P['tex'] not in EXT: continue
    pos, uv, ix = part(P)
    V.append(pos); F.append(ix + off); FP += [k] * len(ix); FUV.append(uv[ix]); off += len(pos)
V = np.vstack(V); F = np.vstack(F); FP = np.array(FP); FUV = np.vstack(FUV)
ext = trimesh.Trimesh(V, F, process=False)
inter = trimesh.ray.ray_pyembree.RayMeshIntersector(ext)
# slices: denser where the shape changes (nose, arches, windshield, roof, spoiler, tail)
ZS = np.array([-2.36, -2.22, -2.07, -1.92, -1.76, -1.56, -1.34, -1.10, -0.85, -0.57, -0.28, 0.06, 0.42, 0.78, 1.08, 1.30, 1.52, 1.74, 1.96, 2.12, 2.26, 2.36])
NT = 17; TH = np.linspace(-1.95, 1.95, NT); CY = 0.72
NZ = len(ZS); G = np.full((NZ, NT, 3), np.nan)
for i, z in enumerate(ZS):
    # every ray comes in from outside toward the centre line: the first thing it meets is the outer skin
    dirs = np.c_[np.sin(TH), np.cos(TH), np.zeros(NT)]; org = np.tile([0, CY, z], (NT, 1)).astype(float) + dirs * 3.0
    locs, ri, ti = inter.intersects_location(org, -dirs, multiple_hits=True)
    for r in range(NT):
        m = (ri == r) & (locs[:, 1] < 1.79)   # (the antenna tip doesn't count; the roof is at ~1.75)
        if m.any(): d = np.linalg.norm(locs[m] - org[r], axis=1); G[i, r] = locs[m][np.argmin(d)]
# over the wheel arches the low rays find nothing: the body's edge lifts there (lower points fold onto the last hit)
for i in range(NZ):
    for half in (range(NT // 2, -1, -1), range(NT // 2, NT)):
        last = None
        for r in half:
            if np.isfinite(G[i, r, 0]): last = G[i, r].copy()
            elif last is not None: G[i, r] = last
# light smoothing along the length (keeps the shape crisp, removes ray noise)
Gs = G.copy()
for i in range(1, NZ - 1): Gs[i] = 0.25 * G[i - 1] + 0.5 * G[i] + 0.25 * G[i + 1]
Gs[:, :, 2] = G[:, :, 2]
# the ends, rounded off by hand (the way a PS1 artist would): one more ring at each end, the last traced outline drawn in
# toward its centre and moved out to the bumper, so the nose is round and the tail square rather than a beak
def endring(r, z, kx, ky):
    c = np.r_[r[:, 0].mean(), r[:, 1].min() + (r[:, 1].max() - r[:, 1].min()) * 0.45, 0]
    out = r.copy(); out[:, 0] = c[0] + (r[:, 0] - c[0]) * kx; out[:, 1] = c[1] + (r[:, 1] - c[1]) * ky; out[:, 2] = z; return out
Gs = np.concatenate([endring(Gs[0], -2.49, 0.78, 0.82)[None], Gs, endring(Gs[-1], 2.47, 0.93, 0.9)[None]], 0)
ZS = np.r_[-2.49, ZS, 2.47]
np.save('/tmp/lp/hull.npy', Gs); np.save('/tmp/lp/zs.npy', ZS)
print('grid', Gs.shape, 'missing', int(np.isnan(Gs).any(2).sum()))
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
fig, ax = plt.subplots(1, 2, figsize=(15, 4.2))
NZ = len(ZS)
for i in range(NZ): ax[0].plot(Gs[i, :, 2], Gs[i, :, 1], 'b-', lw=0.5)
for r in range(NT): ax[0].plot(Gs[:, r, 2], Gs[:, r, 1], 'r-', lw=0.6)
ax[0].set_aspect('equal'); ax[0].set_title('side: the low-poly shell grid')
for i in range(0, NZ, 2): ax[1].plot(Gs[i, :, 0], Gs[i, :, 1], '-', lw=0.8)
ax[1].set_aspect('equal'); ax[1].set_title('cross-sections')
plt.tight_layout(); plt.savefig('/tmp/lp/hull.png', dpi=70)
