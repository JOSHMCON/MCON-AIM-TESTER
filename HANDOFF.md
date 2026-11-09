# Handoff: MCON Sandbox session (Nov 2026)

Josh works on the game across more than one Claude (a personal one and this "OSNAP" one); both edit the
same `index.html`. Always start from the newest file in the repo, and if code you expect looks different,
assume the other session changed it and work *with* those changes rather than over them.

Live preview used during this session: https://claude.ai/artifact/GGu2gcxT9yHW6uFbUdLXBW
(note: controllers don't work in the Claude viewer — use GitHub Pages).

## How Josh likes to work
- Talks by dictation: messages are casual and sometimes garbled ("go Prius" = OG Prius, "oranges" =
  branches). Interpret sensibly; ask one short question only when it truly matters.
- Wants visible results: screenshot and check changes before calling them done. Be honest about trade-offs
  and anything untested.
- Loves the PS1 look (low-res, dithered, chunky) but wants text and UI crisp.
- Fine with big autonomous jobs ("I'm going out, do the big thing").
- Upload flow today: Josh downloads `index.html` and commits it to the repo himself (no write access from
  Claude in chat). In Claude Code, commit/push directly.

## What changed this session (newest file = `index.html` in this packet)
1. **Blurry sign text** (aim-trainer boards):
   - Safety net no longer shrinks the canvas below 1x; it drops light shafts first (`RAYS_ON`).
   - Text pass renders at a fixed **1080 lines**, averaged down with 4 filtered taps (`tq` in the post shader,
     derivatives extension enabled on `postMat`).
   - Signs skip the PS1 vertex snap (`userData.noSnap`), the whole board also draws in the sharp text
     layer, full anisotropic filtering on sign textures.
2. **Black screen in the Claude viewer**: both `getGamepads()` reads wrapped in try/catch.
3. **Performance** (~2x faster frame in profiling):
   - Shadow pass: casters > 150 m culled (`cullFar`) — 2,095 → ~240 draw calls; redraws every other frame.
   - Sign-occlusion depth pass: only objects between you and the signs.
   - Still available (not done): merge/instance the ~2,700 static objects; LOD for distant terrain
     (each pass pushes ~576k triangles, mostly terrain).
4. **New tree style** (test, two trees left of the aim trainer): classic PS1 "cross tree" — a whole spruce
   painted in code on a cut-out texture, on two crossed panels; trunk painted in; foliage stops at a ragged
   hem ~3 m up; see-through holes; each panel of the X a different painting; panels excluded from the shadow
   pass. Not yet scattered across the world (plan: a few variants, shared textures, batched).
5. **PS1 Prius** (default) + **"Prius model: PS1 / OG"** menu row (saves to TUNE, reloads):
   - Outside: the real body shrunk to ~1,500 triangles with gentle repeated passes (same as the interior
     approach), everything baked into one 256x512 texture from straight-on "photos" (left/right/top/front/
     rear): lights, grille, trim, windows, plate, badges. Glass transparency per pixel.
   - Mirrors: two crossed flat cut-out panels each (housing); the small mirror glass stays for live reflections.
   - Kept from the other session: `lp_inner` dark lining (rebuilt for the new shell), lamp glow layers
     `lp_head`/`lp_tail` (rebuilt from lamp masks), 12-sided wheels, the **original full-detail interior**
     (Josh loves it — leave it alone).
   - ~1,700 triangles outside; ~12.8k total (mostly interior). OG Prius ~22.3k.
   - Pipeline + scripts in `tools/prius/` (see `docs/prius-ps1.md`).

## Open items / ideas
- Scatter the cross trees across the world (variants, batching).
- Lower-poly weapons, house, cars (Josh's "PS1 direction"); possibly a "PS1 budget mode".
- Speed steps 3–4 (merge static objects, terrain LOD).
- PS1 Prius polish if asked: chin under the front bumper reads dark; window edges slightly jagged.
- The cave/bridge/race-island work from an older file version was never ported to this file.

## Other things from this session (outside the game)
- **MCON Lite write-up**: final text in `docs/mcon-lite-writeup.md`.
- A separate studio page for an RC short-course truck + Josh's LiDAR scan of his own truck, cleaned and
  rebuilt: https://claude.ai/artifact/RyVYBhjwb69HbDXbQAN1Qr (not part of this repo).
- A drop-in `prius-model.js` exists from an earlier round (original Prius as a self-contained module).
