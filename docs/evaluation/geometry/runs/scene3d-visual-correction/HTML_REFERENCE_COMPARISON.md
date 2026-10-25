# Owner HTML reference vs AlgoSim Scene3D

Reference: `docs/evaluation/geometry/runs/visual-closure-hybrid-readiness/reference/matphang.html` ("Mô Phỏng Hình Học
Không Gian 3D – Lớp 11 & 12"), three.js r128, 18 shapes.

## 1. Identity of the reference (the hash question Codex left open)

| Bytes | SHA-256 |
|---|---|
| Committed blob (`git show HEAD:…/matphang.html`) | `279216192b09d6e12c8b8d444dcb0bf943419e6c52078fe04107684f0d9e8af1`. This is the hash cited by `HTML_18_FAMILY_CAPABILITY_MATRIX.md`, `catalog-audit.json` and `PACKAGE_MANIFEST.json` |
| This checkout's working copy, 211 386 bytes | `1cc6e74c9c69afc795c2f8fa7d17117d6eb33f22e7f3dcd462e287e3924d5491` |
| Working copy with CRLF→LF | `279216192b09…` again |

`git ls-files --eol` reports `i/lf w/crlf`. Git stores the file with LF, and this Windows checkout converts it to CRLF
on checkout. The reference is byte-identical to the one the earlier reports cite. The "bytes differ" note in Codex's
ledger is only line endings.

## 2. Execution

Codex ran the original, unmodified HTML in headless Chrome (`tools/reference-browser.mjs`). Result: 18/18 shapes, 0
page errors, 0 CDN failures, 0 model calls. Screenshots and counters are in `verification/reference/receipt.json`. For
every shape the shell opacity is 0.12, there is one canvas, and labels number 7–17. The reference was used as a design
reference, never as an oracle.

## 3. What was compared, and the decision

| Aspect | Reference (`matphang.html`) | AlgoSim before | Decision |
|---|---|---|---|
| Stroke primitive | Every edge, arc and silhouette is a world-space **tube** (`CylinderGeometry`, r ≈ 0.022–0.028). A tube keeps screen width from every angle | Polyhedron edges are fat lines. Circle/ellipse rims are a **flat ribbon in the region's own plane**, which collapses below 1 px when that plane is seen obliquely (measured: p6 ellipse, "quarter" camera, 390 px — the hidden arc vanished) | **Port the property, not the primitive.** Every rim chord now also gets a 1 px stroke along the outer curve that cannot collapse, with the same material, colour, dash and depth as the ribbon. No tubes: the reference pre-builds two meshes per chord (192 draw objects per rim), while the stroke reuses the rim's existing in-place buffers and adds two objects per rim |
| Hidden lines | Dashed by drawing every second short segment (`i % 2`), opacity 0.68 | Same idea: hidden rim chords dashed `i % 4 < 2`, hidden opacity 0.65 | Kept. Already equivalent |
| Shell | Opacity 12 % | ~12 % shell | Kept |
| Section colours | Terracotta `0xC85A32` rim and fill; purple plane `0x6D28D9`; cobalt `0x2563EB` for lines/angles | Terracotta fill, purple auxiliary plane, cobalt selected boundary (Owner policy F2) | Kept the AlgoSim role mapping (cobalt = *selected* boundary, not a category colour) |
| Visibility of arcs | Per-mode shortcuts: `lateral_split` (radial normal · view), `cylinder_top` (`camera.y > center.y`), cone slope normal for vertical cones only | Exact ray/finite-volume test (`diemVanhCongBiChe`) in any axis orientation, the same classifier for lines and rims | **Rejected the shortcuts.** They assume a vertical axis |
| Occlusion by cylinder/cone | Ray sampled at ~11 fixed parameters, radius shrunk by 0.02, height margins 0.015 | Closed-form ray–cylinder/cone/cap intersection | **Rejected.** Sampling misses thin crossings, and the fixed margins are scale-dependent |
| Silhouette generators | Tangent angle `acos(r / horizontalDistance)`, clamped to 0.98, applied to cones too, vertical axis only | Exact tangent generators for any axis. Tests assert `normal · (eye − p) = 0` | **Rejected for cones.** The cylinder formula is wrong for a cone (its silhouette depends on camera height) |
| Answers | Final values shown immediately as decimals (`108.37`, `77.41`) on side cards | Mode A: no final answer anywhere. Mode B: answer once, in exact form | **Not ported.** Pedagogical choice of AlgoSim (exact arithmetic, answer privacy) |
| Interaction | Sliders change geometry (radius, height, cut position) | Select and scrub only; geometry is the backend's | **Not ported.** Dragging geometry is outside scope (invariant #31 `frame k ⇔ trace[k]`; R0: the frontend never decides coordinates) |
| Right-angle marks, labels | Present, cobalt/green | Present, role-coloured; labels avoid overlap | No change needed |

## 4. What the comparison changed in the product

1. Rim stroke that survives oblique views (reference lesson: stroke width must not depend on the region's plane).
2. Front rim drawn in the same render queue as solid outlines, so the selected boundary stays on top. In the reference,
   tubes are depth-tested meshes, so the nearer one simply wins. In AlgoSim the cylinder silhouette was overdrawing the
   selected ellipse near tangency.

Both changes are in `SCENE3D_VISIBILITY_CORRECTION.md` with their tests and browser evidence.
