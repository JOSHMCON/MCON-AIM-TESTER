import json, base64, numpy as np, fast_simplification as fs, trimesh
D = json.load(open('/tmp/lp/prius.json')); lo = np.array(D['lo']); hi = np.array(D['hi'])
dec = (lambda s, t: np.frombuffer(base64.b64decode(s), t))
enc = (lambda a: base64.b64encode(np.ascontiguousarray(a).tobytes()).decode())
BUDGET = {'priusvolan.tga': 90, 'priuswheel2.tga': 200, 'Brakes.tga': 48, 'priusint5.tga': 220, 'priusparts1.tga': 1100,
          'priusint1.tga': 320, 'priusint3.tga': 60, 'priusint2.tga': 160, 'prius2.tga': 90, 'prius1.tga': 50, 'prius_doorhandle.tga': 24, 'prius_rim.tga': 140, 'prius_body.tga': 520}
out = dict(D); out['parts'] = []; total = 0
for P in D['parts']:
    key = P['key']
    q = dec(P['p'], np.int16).reshape(-1, 3).astype(np.float64); opos = lo + (q + 32768) / 65535 * (hi - lo)
    ouv = dec(P['uv'], np.float32).reshape(-1, 2).astype(np.float64)
    oix = dec(P['ix'], np.uint32 if P['i32'] else np.uint16).reshape(-1, 3).astype(np.int64)
    target = BUDGET.get(key)
    if target is None or len(oix) <= target:   # small parts stay exactly as they are
        out['parts'].append(P); total += len(oix); continue
    # weld coincident vertices into one continuous surface
    keyp = np.round(opos / 2e-4).astype(np.int64); _, first, inv = np.unique(keyp, axis=0, return_index=True, return_inverse=True)
    pos = opos[first]; ix = inv.ravel()[oix]; ix = ix[(ix[:, 0] != ix[:, 1]) & (ix[:, 1] != ix[:, 2]) & (ix[:, 0] != ix[:, 2])]
    pos_w = pos
    # small separate pieces (a licence plate, a badge, a strip of trim) are kept exactly; only the big ones get simplified
    comps = trimesh.graph.connected_components(trimesh.graph.face_adjacency(ix), nodes=np.arange(len(ix)), min_len=1)
    small = np.zeros(len(ix), bool)
    for cpt in comps:
        if len(cpt) <= 40: small[cpt] = True
    keep_ix = ix[small]; ix = ix[~small]; target = max(20, target - len(keep_ix))
    # gentle passes, repeated until the budget is reached (each pass only takes the safest collapses)
    for _ in range(40):
        if len(ix) <= target: break
        red = 1 - target / len(ix); p2, f2 = fs.simplify(pos.astype(np.float32), ix.astype(np.int32), target_reduction=min(red, 0.35), agg=3)
        p2 = np.asarray(p2, np.float64); f2 = np.asarray(f2, np.int64)
        if len(f2) >= len(ix) * 0.995: break
        pos, ix = p2, f2
    # put the kept small pieces back (their vertices appended to the simplified ones)
    if len(keep_ix):
        used = np.unique(keep_ix); remap = -np.ones(len(wpos_all := pos_w), np.int64); remap[used] = np.arange(len(used)) + len(pos)
        kp = pos_w[used].copy()
        kf = np.cross(pos_w[keep_ix[:, 1]] - pos_w[keep_ix[:, 0]], pos_w[keep_ix[:, 2]] - pos_w[keep_ix[:, 0]]); kn = np.zeros_like(pos_w)
        for c in range(3): np.add.at(kn, keep_ix[:, c], kf)
        kn = kn[used]; kn /= np.maximum(np.linalg.norm(kn, axis=1, keepdims=True), 1e-12)
        kp += kn * 0.004   # small details sit a few mm proud, so the simplified panel under them can't swallow them
        pos = np.vstack([pos, kp]); ix = np.vstack([ix, remap[keep_ix]])
    # smooth normals from the welded result
    fn = np.cross(pos[ix[:, 1]] - pos[ix[:, 0]], pos[ix[:, 2]] - pos[ix[:, 0]]); vn = np.zeros_like(pos)
    for c in range(3): np.add.at(vn, ix[:, c], fn)
    vn /= np.maximum(np.linalg.norm(vn, axis=1, keepdims=True), 1e-12)
    # texture coordinates per triangle: all three corners from the one original triangle it sits on (no island mixing)
    om = trimesh.Trimesh(opos, oix, process=False)
    cen = pos[ix].mean(1); _, _, tri = trimesh.proximity.closest_point(om, cen)
    ot = opos[oix[tri]]                                      # (F, 3, 3) original triangle corners
    corners = pos[ix]                                        # (F, 3, 3) new corners
    F = len(ix); fp = corners.reshape(-1, 3); rep_tri = np.repeat(ot, 3, axis=0)
    bary = trimesh.triangles.points_to_barycentric(rep_tri, fp)
    uvt = np.repeat(ouv[oix[tri]], 3, axis=0)              # (3F, 3, 2)
    fuv = (uvt * bary[:, :, None]).sum(1)
    fnrm = vn[ix].reshape(-1, 3)
    n = len(fp); big = n >= 65536
    qp = np.clip(np.round((fp - lo) / (hi - lo) * 65535 - 32768), -32768, 32767).astype(np.int16); qn = np.round(fnrm * 127).astype(np.int8)
    out['parts'].append({'key': key, 'tex': P['tex'], 'color': P['color'], 'n': int(n), 'i32': int(big), 'p': enc(qp), 'nm': enc(qn), 'uv': enc(fuv.astype(np.float32)), 'ix': enc(np.arange(n, dtype=np.uint32 if big else np.uint16))})
    total += F; print(f"{key[:26]:26s} {len(oix):5d} -> {F:4d} tris")
print('total triangles', total)
json.dump(out, open('/tmp/lp/prius_lp_geo.json', 'w'))
