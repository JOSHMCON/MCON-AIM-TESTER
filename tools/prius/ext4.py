exec(open('/tmp/lp/ext2.py').read().split("# ---- assign every face")[0])
# which part of the real car each texel was photographed from (to find the lamps)
SRC = np.full((1024, 512), -1, np.int64)
for v, (axis, sgn, x0, y0, w, h) in VIEWS.items():
    yy, xx = np.mgrid[y0:y0 + h, x0:x0 + w]; a = (xx + 0.5 - x0) / PPM; b = (yy + 0.5 - y0) / PPM
    if v == 'left':  org = np.c_[np.full(a.size, -4), Y1 - b.ravel(), Z0 + a.ravel()]; dr = [1, 0, 0]
    if v == 'right': org = np.c_[np.full(a.size, 4), Y1 - b.ravel(), Z1 - a.ravel()]; dr = [-1, 0, 0]
    if v == 'top':   org = np.c_[X0 + b.ravel(), np.full(a.size, 4), Z0 + a.ravel()]; dr = [0, -1, 0]
    if v == 'front': org = np.c_[X0 + a.ravel(), Y1 - b.ravel(), np.full(a.size, -5)]; dr = [0, 0, 1]
    if v == 'rear':  org = np.c_[X1 - a.ravel(), Y1 - b.ravel(), np.full(a.size, 5)]; dr = [0, 0, -1]
    locs, ri, ti = inter.intersects_location(org.astype(float), np.tile(dr, (len(org), 1)).astype(float), multiple_hits=False)
    src = np.full(len(org), -1); src[ri] = FP[ti]; SRC[y0:y0 + h, x0:x0 + w] = src.reshape(h, w)
head_k = [k for k, P in enumerate(D['parts']) if P['tex'] == 'prius1.tga'][0]; tail_k = [k for k, P in enumerate(D['parts']) if P['tex'] == 'prius2.tga'][0]
np.save('/tmp/lp/head_mask.npy', SRC == head_k); np.save('/tmp/lp/tail_mask.npy', SRC == tail_k)
print('headlight texels', int((SRC == head_k).sum()), '| tail-light texels', int((SRC == tail_k).sum()))
