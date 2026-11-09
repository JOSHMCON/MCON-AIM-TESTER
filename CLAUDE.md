# MCON Sandbox (MCON-AIM-TESTER)

A single-file, browser-based PS1-style 3D sandbox built by Josh to show off and test **MCON**, his phone
game controller. Aim trainer, an explorable world, a drivable short-course truck and a drivable 2004 Prius.
Repo: https://github.com/JOSHMCON/MCON-AIM-TESTER — served by GitHub Pages from `index.html`.

Read `HANDOFF.md` for the full history of the last session, open items and how Josh likes to work.

## The one file
Everything lives in `index.html` (~4.3 MB, ~11k lines): HTML, CSS, one big script, and embedded data
(the Prius models and textures are base64 JSON blobs: `PRIUS_DATA` = original, `PRIUS_LP` = PS1 version).
- three.js **r128** from cdnjs (classic global `THREE`, not modules). Google Fonts. Nothing else external.
- Never reformat the file or rewrite large regions. Make small, targeted edits.

## Rendering (the "PS1 look")
- `ps1Render()` does all passes each frame: `shadowPass()` (sun shadow map) → world into `lowRT`
  (240-line, PS1 materials with vertex snap, affine-ish warp, dithering) → **sign text** into `textRT`
  (always 1080 lines, then averaged down; signs bypass the PS1 filter) → gun → post shader to screen.
- PS1 materials: `MeshToonMaterial` etc. are patched (`PS1Mat`, `PS1_PATCH`). `material.userData.noSnap`
  turns off the vertex snap for one material (used by the signs).
- Performance safety net (search `let pr = Math.min(devicePixelRatio`): when frames run slow it first
  turns off light shafts (`RAYS_ON`), then lowers resolution — never below 1x (smaller blurs sign text).
- `cullFar(cx, cz, R)` hides far objects for a single pass: used by the shadow pass (casters > 150 m)
  and the sign-occlusion depth pass. Instanced meshes and always-draw objects are never culled.
- The shadow map redraws every other frame.

## Where things are (search for these)
| What | Search |
|---|---|
| Prius model builder (top level) | `function buildPriusModel(THREE, options)` — takes `options.data` |
| Prius assembly, materials, lamps, wheels | `function buildPriusInto(` — `const PD = TUNE.priusHD ? PRIUS_DATA : PRIUS_LP` |
| PS1 Prius parts | keys `lp_shell`, `lp_inner`, `lp_head`, `lp_tail`; mirror glass `color:prmirror` (live reflections) |
| Menu (both lists) | `function menuItems()` — includes `label: 'Prius model'` (PS1/OG, saves + reloads) |
| Tuning / saved settings | `TUNE_DEF`, `TUNE_KEY = 'mcon-truck-tune'` (localStorage), `tuneSave()` |
| Test cross trees | `function crossTree(x, z, o)` — two at (-5.2,-1.5) and (-9.6,0.6), left of the aim trainer |
| Aim-trainer sign trees | `placeTreeAt(board.menu…` / `placeBoard()`; sign text layer `TEXT_LAYER` |
| Sign visibility for the text pass | `function signsInView()` (90 m, idle phase only) |
| Vehicle switch | `setVehicle('prius' | 'truck')`, vehicle object `K` (`K.S` = physics state) |
| M Island (past the tunnel) | `const ISK =` (Josh's drawing px → world, 3.1 m/px), `const ISLE =` (shore distance field), `isleU`/`isleH`, `NECK` |
| Island track | `const TRACK = (() =>` — `LAP` points tagged L dirt / A air / W water, `F` jumps (kicker/landing), `LOOP`; `trackAt` skips air/water |
| Island build + per frame | `function buildPeninsula(` (ground tiles `IGRID`, ribbon, buoys, `buildLoops`), `updateIsle` (hides far pieces), `loopRide` (the wooden loop) |
| Controller | two `navigator.getGamepads()` reads, both wrapped in try/catch (see below) |

## Hard-won rules
- **Gamepad:** the Claude artifact viewer blocks the Gamepad API (permissions policy) — it *throws*.
  Every `getGamepads()` call must stay inside try/catch, or a frame aborts and the game goes black.
  Controllers work on GitHub Pages, not inside the Claude viewer.
- **Edits:** when patching with a script, assert each old string occurs exactly once before replacing;
  if a line appears twice (e.g. the two menu lists), handle it deliberately.
- **After every edit:** extract the `<script>` blocks and run `node --check` on them.
- **Then test in a real browser** (see `tools/test/`): load, check `pageerror`/console errors, screenshot.
  Look at the screenshots — most bugs here are visual.
- The game is GPU-bound, not logic-bound (profiled: JS logic is negligible). Draw calls in the shadow pass
  were the big cost; keep an eye on draw calls and triangles per pass (`tools/test/profile_frame.py`).

## Testing setup
- Headless Chromium via Playwright with `--use-gl=swiftshader --enable-webgl --ignore-gpu-blocklist`
  (software GL: ~20 fps, slow — render on demand where possible).
- Make a test copy with local three.js and debug hooks: `python3 tools/test/make_test_copy.py`
  (see `tools/test/README.md`). Click `#playBtn`, wait ~15 s for the world to build, click `#expandBtn`.

## Deploy
Commit `index.html` to the repo root (GitHub Pages, `.nojekyll` present). Pages updates in a minute or two.
