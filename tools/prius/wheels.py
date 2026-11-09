exec(open('/tmp/lp/hull.py').read().split("EXT = [")[0])
WC = [[-0.855, -1.559], [0.855, -1.559], [-0.855, 1.535], [0.855, 1.535]]; WY = 0.3665; R = 0.367; XO, XI = -0.985, -0.73; N = 12
TEX = {t: np.array(Image.open(io.BytesIO(base64.b64decode(v['uri'].split(',', 1)[1]))).convert('RGBA')) for t, v in D['tex'].items()}
# the detailed front-left wheel, as one mesh, to bake from
V, F, FP, FUV = [], [], [], []; off = 0
for k, P in enumerate(D['parts']):
    if P['tex'] not in ('priuswheel2.tga', 'prius_rim.tga', 'Brakes.tga'): continue
    pos, uv, ix = part(P); keep = (pos[ix].mean(1)[:, 0] < 0) & (pos[ix].mean(1)[:, 2] < 0)
    V.append(pos); F.append(ix[keep] + off); FP += [k] * int(keep.sum()); FUV.append(uv[ix[keep]]); off += len(pos)
wm = trimesh.Trimesh(np.vstack(V), np.vstack(F), process=False); FP = np.array(FP); FUV = np.vstack(FUV)
wint = trimesh.ray.ray_pyembree.RayMeshIntersector(wm)
def col(pts, tri, dark=(18, 18, 20)):
    out = np.tile([*dark, 255], (len(pts), 1)).astype(float); bary = trimesh.triangles.points_to_barycentric(wm.triangles[tri], pts); uv = (FUV[tri] * bary[:, :, None]).sum(1)
    for k in np.unique(FP[tri]):
        m = FP[tri] == k; im = TEX[D['parts'][k]['tex']]; H, W = im.shape[:2]
        c = im[np.clip(((1 - uv[m, 1] % 1) * H).astype(int), 0, H - 1), np.clip(((uv[m, 0] % 1) * W).astype(int), 0, W - 1)].astype(float)
        c[c[:, 3] < 110] = [*dark, 255]; c[:, 3] = 255; out[m] = c
    return out
S = 128; at = np.zeros((S, S, 4)); at[:, :, 3] = 255; vv, uu = np.mgrid[0:S, 0:S]; U = (uu + 0.5) / S; Vt = 1 - (vv + 0.5) / S
z0 = WC[0][1]
m = Vt >= 0.5   # the tread band, all the way round
a = U[m] * 2 * np.pi; xx = XO + (XI - XO) * (Vt[m] - 0.5) / 0.5
pts = np.c_[xx, WY + R * np.cos(a), z0 + R * np.sin(a)]; cp, _, tri = trimesh.proximity.closest_point(wm, pts); at[m] = col(cp, tri)
m = (Vt < 0.5) & (U < 0.5)   # the outer face: the rim, seen straight on
du, dv = (U[m] - 0.25) / 0.24, (Vt[m] - 0.25) / 0.24; inside = du * du + dv * dv <= 1.0
org = np.c_[np.full(len(du), -1.6), WY + dv * R, z0 + du * R]; locs, ri, ti = wint.intersects_location(org, np.tile([1.0, 0, 0], (len(du), 1)), multiple_hits=False)
c = np.tile([18, 18, 20, 255], (len(du), 1)).astype(float)
if len(ri): c[ri] = col(locs, ti)
at[m] = c
at[(Vt < 0.5) & (U >= 0.5)] = [22, 22, 24, 255]   # the inner face: dark
Image.fromarray(at.astype(np.uint8)).save('/tmp/lp/wheel_atlas.png')
# geometry: four 12-sided wheels
P, UV, IX = [], [], []
def v(p, t): P.append(p); UV.append(t); return len(P) - 1
for q, (wx, wz) in enumerate(WC):
    s = -1 if wx < 0 else 1; xo, xi = wx + s * (abs(XO) - 0.855), wx - s * (0.855 - abs(XI))
    ang = [2 * np.pi * k / N for k in range(N + 1)]
    for k in range(N):   # tread
        a0, a1 = ang[k], ang[k + 1]
        p = lambda x, a: [x, WY + R * np.cos(a), wz + R * np.sin(a)]
        i0, i1, i2, i3 = v(p(xo, a0), [k / N, 0.5]), v(p(xo, a1), [(k + 1) / N, 0.5]), v(p(xi, a0), [k / N, 1.0]), v(p(xi, a1), [(k + 1) / N, 1.0])
        IX += [[i0, i2, i1], [i1, i2, i3]]
    for x, cu, out in ((xo, 0.25, True), (xi, 0.75, False)):   # outer and inner faces
        c = v([x, WY, wz], [cu, 0.25]); rim = [v([x, WY + R * np.cos(a), wz + R * np.sin(a)], [cu + 0.24 * np.sin(a) * (-s if out else 1), 0.25 + 0.24 * np.cos(a)]) for a in ang[:N]]
        for k in range(N): IX.append([c, rim[k], rim[(k + 1) % N]])
P = np.array(P); UV = np.array(UV); IX = np.array(IX)
# outward winding (tread away from the axle, faces away from the wheel centre)
cen = P[IX].mean(1); nrm = np.cross(P[IX[:, 1]] - P[IX[:, 0]], P[IX[:, 2]] - P[IX[:, 0]])
wcen = np.array([[WC[0 if c[2] < 0 and c[0] < 0 else 1 if c[2] < 0 else 2 if c[0] < 0 else 3][0], WY, WC[0 if c[2] < 0 and c[0] < 0 else 1 if c[2] < 0 else 2 if c[0] < 0 else 3][1]] for c in cen])
flip = (nrm * (cen - wcen)).sum(1) < 0; IX[flip] = IX[flip][:, [0, 2, 1]]
np.savez('/tmp/lp/wheels.npz', P=P, UV=UV, IX=IX); print('wheels: triangles', len(IX))
