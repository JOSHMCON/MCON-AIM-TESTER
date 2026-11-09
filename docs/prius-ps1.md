# How the PS1 Prius was built

Goal: a PS1-era car — few polygons, detail painted into one small texture — while keeping the game's Prius
features (paint colour, glowing lamps, live mirror glass, sliding seat, dash screen, steering, wheels).

## What worked (current version)
1. **Shrink the real outside, gently.** Merge the outside parts (paint, trim, glass, lights, handles, badges),
   cut away the mirror housings, weld coincident vertices into one surface, then run `fast_simplification`
   with a *gentle* setting (agg=3) repeatedly until ~1,500 triangles. Aggressive settings or simplifying
   unwelded patches wreck the panels. (`tools/prius/ext1.py`)
2. **Bake everything into one texture** from straight-on "photos": every face is assigned to the view it
   faces most (left/right/top/front/rear, downward faces = dark underside) and gets planar UVs into that
   view's region of a 512x1024 sheet; each region is filled by casting rays at the real car and copying the
   colour it hits. Paint becomes white (the game tints it), glass keeps per-pixel transparency and a dark tint,
   see-through badge pixels show paint. (`ext2.py`). xatlas unwrapping segfaulted on the welded mesh,
   hence the PS1-style view projection.
3. **Mirrors as flat cut-outs**: front and side "photos" of each mirror housing on the same sheet, on two
   crossed double-sided panels. (`ext3.py`)
4. **Lamp masks** record which texels came from the real head/tail lights (`ext4.py`), used for the glow
   layers. `merge.py` builds `lp_shell`, `lp_inner` (lining), `lp_head`, `lp_tail` into the game's
   `PRIUS_LP` and keeps wheels, mirror glass and the original interior from the current file.
5. Final texture: 256x512, 64 colours, nearest sampling (`ps1` flag in the data).

## What didn't
- Simplifying each part separately without welding → holes in panels; thin trim strips vanish first.
- A traced "loft" shell (`hull.py`, slices + rays) looked clean in profile but smeared on the steep nose/tail.

## Running the scripts
They expect working files in `/tmp/lp/` (adjust paths at the top if needed). Start with
`python3 extract_prius.py index.html` to write `/tmp/lp/prius.json` (the original model). Needs
`pip install trimesh rtree embreex fast-simplification scipy pillow numpy`.
Order: `ext1.py` → `ext2.py` → `ext3.py` → `ext4.py` → (`wheels.py` for the wheel atlas) → `assemble3.py` → `merge.py`.
`merge.py` writes straight into the game file — commit first.
