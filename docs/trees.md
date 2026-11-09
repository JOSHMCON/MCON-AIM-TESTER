# Cross trees (PS1 style)

`crossTree(x, z, o)` in index.html paints a whole spruce on a canvas (trunk included) and puts it on two
flat panels crossed in an X (MeshBasicMaterial, alphaTest 0.5, DoubleSide, nearest filtering).
Each panel gets its own painting (seed and seed+101). Options:
`seed, W (canvas width; height 256), height (m), bare (fraction of clear trunk at the bottom), trunk (px),
step (branch-layer spacing), shape (silhouette exponent), puff (clump size), stray (twigs), gaps (skipped
layers), holes (see-through slivers), turn (rotation), greens (palette)`.
Foliage is clipped to a ragged hem above the trunk (no flat dark wall at the base). Panels are pushed to
`noShadow` (no square shadows). Collision via `solidTrees` (kind 'pillar').
Josh's references: Silent Hill-style PS1 spruces, but summer green, dense, jagged, with see-through gaps.
