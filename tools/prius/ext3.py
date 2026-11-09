exec(open('/tmp/lp/ext2.py').read().split("# ---- assign every face")[0])
S = np.load('/tmp/lp/sheet.npy'); E = np.load('/tmp/lp/ext2.npz'); P, UV, IX = list(E['P']), list(E['UV']), list(E['IX'])
full, FPa, FUVa, _ = mesh_of(EXT + ['color:prmirror'])
mk = [i for i, Pp in enumerate(D['parts']) if Pp['key'] == 'color:prmirror'][0]; mpos, _, _ = part(D['parts'][mk])
MP = 200.0   # px per metre on the mirror images
slot = 0
for sx in (-1, 1):
    m = (np.sign(mpos[:, 0]) == sx) & (np.abs(mpos[:, 0]) > 0.6); g0, g1 = mpos[m].min(0), mpos[m].max(0)
    b0 = g0 - [0.06, 0.07, 0.10]; b1 = g1 + [0.06, 0.07, 0.06]; b0[0] = min(b0[0], g0[0]) if sx > 0 else b0[0]
    if sx < 0: b1[0] = -0.86
    else: b0[0] = 0.86
    c = full.triangles_center; keep = (c > b0).all(1) & (c < b1).all(1)
    sub = trimesh.Trimesh(full.vertices, full.faces[keep], process=False); sFP = FPa[keep]; sFUV = FUVa[keep]; sint = trimesh.ray.ray_pyembree.RayMeshIntersector(sub)
    ctr = (b0 + b1) / 2
    for view in ('front', 'side'):
        if view == 'front': wa, hb = b1[0] - b0[0], b1[1] - b0[1]
        else: wa, hb = b1[2] - b0[2], b1[1] - b0[1]
        W, H = int(np.ceil(wa * MP)), int(np.ceil(hb * MP)); x0, y0 = slot * 64, 700; slot += 1
        yy, xx = np.mgrid[0:H, 0:W]; a = (xx + 0.5) / MP; b = (yy + 0.5) / MP
        if view == 'front': org = np.c_[b0[0] + a.ravel(), b1[1] - b.ravel(), np.full(a.size, -5.0)]; dr = [0, 0, 1]
        else: org = np.c_[np.full(a.size, sx * 4.0), b1[1] - b.ravel(), b0[2] + a.ravel()]; dr = [-sx, 0, 0]
        locs, ri, ti = sint.intersects_location(org, np.tile(dr, (len(org), 1)).astype(float), multiple_hits=False)
        col = np.zeros((len(org), 4))
        if len(ri): col[ri] = colour(sub, sFP, sFUV, locs, ti); col[ri, 3] = 255
        S[y0:y0 + H, x0:x0 + W] = col.reshape(H, W, 4)
        # the flat panel (both faces), carrying that image
        if view == 'front':
            q = [[b0[0], b0[1], ctr[2]], [b1[0], b0[1], ctr[2]], [b1[0], b1[1], ctr[2]], [b0[0], b1[1], ctr[2]]]
            quv = [[x0, y0 + H], [x0 + W, y0 + H], [x0 + W, y0], [x0, y0]]
        else:
            q = [[ctr[0], b0[1], b0[2]], [ctr[0], b0[1], b1[2]], [ctr[0], b1[1], b1[2]], [ctr[0], b1[1], b0[2]]]
            quv = [[x0, y0 + H], [x0 + W, y0 + H], [x0 + W, y0], [x0, y0]]
        ids = []
        for p, (u, v) in zip(q, quv): P.append(np.array(p)); UV.append(np.array([u / 512.0, 1 - v / 1024.0])); ids.append(len(P) - 1)
        IX += [[ids[0], ids[1], ids[2]], [ids[0], ids[2], ids[3]], [ids[0], ids[2], ids[1]], [ids[0], ids[3], ids[2]]]
    print('mirror', sx, 'box', b0.round(2), b1.round(2))
P = np.array(P); UV = np.array(UV); IX = np.array(IX)
np.save('/tmp/lp/sheet2.npy', S); np.savez('/tmp/lp/ext3.npz', P=P, UV=UV, IX=IX)
Image.fromarray(S[690:780, 0:260].astype(np.uint8)).resize((780, 270), Image.NEAREST).save('/tmp/lp/mirrors.png')
print('shell + mirror panels:', len(IX), 'triangles')
