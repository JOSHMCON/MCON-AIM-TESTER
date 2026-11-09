import json, base64, numpy as np, fast_simplification as fs, trimesh, xatlas
exec(open('/tmp/lp/hull.py').read().split("EXT = [")[0])
EXT = ['prius_body.tga', 'prius_doorhandle.tga', 'priusparts1.tga', 'priusglass1.tga', 'prius1.tga', 'prius2.tga', 'priuslogo2.tga']
# the mirrors: where the mirror glass is, plus a margin for the housing
mk = [i for i, P in enumerate(D['parts']) if P['key'] == 'color:prmirror'][0]; mpos, _, mix = part(D['parts'][mk])
boxes = []
for sx in (-1, 1):
    m = (np.sign(mpos[:, 0]) == sx) & (np.abs(mpos[:, 0]) > 0.6); b0, b1 = mpos[m].min(0), mpos[m].max(0)   # only the door mirrors (not the rear-view mirror in the middle)
    boxes.append((b0 - [0.06, 0.07, 0.10], b1 + [0.06, 0.07, 0.06])); print('mirror', sx, 'box', b0.round(2), b1.round(2))
V, F = [], []; off = 0
for P in D['parts']:
    if P['tex'] not in EXT: continue
    pos, uv, ix = part(P); V.append(pos); F.append(ix + off); off += len(pos)
V = np.vstack(V); F = np.vstack(F)
cen = V[F].mean(1); inMirror = np.zeros(len(F), bool)
for b0, b1 in boxes:
    inside = (cen > b0).all(1) & (cen < b1).all(1) & (np.abs(cen[:, 0]) > min(abs(b0[0]), abs(b1[0])) + 0.02)   # only the bits sticking out past the door
    inMirror |= inside
print('faces moved to the flat mirror cut-outs:', int(inMirror.sum()))
F = F[~inMirror]
# weld into one continuous surface, then gentle repeated passes (as the interior)
k = np.round(V / 2e-4).astype(np.int64); _, first, inv = np.unique(k, axis=0, return_index=True, return_inverse=True)
pos = V[first]; ix = inv.ravel()[F]; ix = ix[(ix[:, 0] != ix[:, 1]) & (ix[:, 1] != ix[:, 2]) & (ix[:, 0] != ix[:, 2])]
print('merged outside:', len(ix), 'triangles')
TARGET = 1400
for _ in range(60):
    if len(ix) <= TARGET: break
    p2, f2 = fs.simplify(pos.astype(np.float32), ix.astype(np.int32), target_reduction=min(1 - TARGET / len(ix), 0.3), agg=3)
    p2 = np.asarray(p2, np.float64); f2 = np.asarray(f2, np.int64)
    if len(f2) >= len(ix) * 0.995: break
    pos, ix = p2, f2
used = np.unique(ix); rm = -np.ones(len(pos), np.int64); rm[used] = np.arange(len(used)); pos = pos[used]; ix = rm[ix]
print('simplified outside:', len(ix), 'triangles,', len(pos), 'vertices')
# clean up (no duplicate or zero-area faces) before unwrapping
tm = trimesh.Trimesh(pos, ix, process=True); tm.update_faces(tm.nondegenerate_faces()); tm.update_faces(tm.unique_faces()); tm.remove_unreferenced_vertices()
pos, ix = np.asarray(tm.vertices), np.asarray(tm.faces); print('cleaned:', len(ix), 'triangles')
np.savez('/tmp/lp/ext_pre.npz', P=pos, IX=ix)
# unwrap onto one texture sheet
atl = xatlas.Atlas(); atl.add_mesh(pos.astype(np.float32), ix.astype(np.uint32))
po = xatlas.PackOptions(); po.resolution = 512; po.padding = 2; po.bilinear = True
atl.generate(pack_options=po); vmap, ixu, uvs = atl[0]
upos = pos[vmap]
print('unwrapped:', len(upos), 'vertices,', len(ixu), 'triangles | uv range', uvs.min(0).round(3), uvs.max(0).round(3))
np.savez('/tmp/lp/ext1.npz', P=upos, IX=ixu.astype(np.int64), UV=uvs.astype(np.float64), boxes=np.array([np.r_[b0, b1] for b0, b1 in boxes]))
