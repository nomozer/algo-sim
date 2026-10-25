# F2 role-aware oracle — decision report

Authorization `GO_LOCAL_F2_POLICY_REVIEW_B3_VERIFICATION_SPHERE_SOURCE_FIX`, 2026-10-25.

**Decision: the locked official-suite oracle is NOT changed. The official Visual suite stays 7/8.** The role-aware check
is delivered as a measured proposal. Owner condition 6 (independent review of the checker diff) is not met: the only
review run was a separate-context AI review, and it found five ways the proposal can be wrong (below).

## Owner policy under test

Terracotta `#C85A32` is the section's semantic colour. Cobalt `#2563EB` is the boundary/halo signal of the selected
section. Hover is transient, selection persists. Geometry and provenance must not change.

## Why the locked gate fails this policy

`assessCausalCanvasHues` (`frontend/scripts/compiler-scene-replay-lib.mjs:683`) counts every orange-band pixel of a
selected-state frame. Orange is allowed only when an object in tier `du_kien_so`/`trung_gian` is drawn. When the
section itself is the target (`dich`), its terracotta fill is counted as a violation.

Re-measured in one uninterrupted run, 1440 and 390 px, on three successive candidates with the same outcome — `6c1befcd`, `96a81e08`, and the final integrated `63faa5af` (product `9ced3d27`, measured `ee474c81…`):

| Family | Result |
|---|---|
| triangular_pyramid, triangular_prism, rectangular_pyramid, cuboid, cube, regular_square_pyramid, regular_triangular_pyramid | PASS |
| cross_section | FAIL, desktop and mobile. The only failing nodes are `causal_closure.visual.canvas_role_hues.cam` and the dependent `evidence_gates`. Every mathematical, causal-closure, dash, witness, identity and refusal assertion passes. |

Evidence: `visual/official-run-63faa5af/BROWSER_EVIDENCE.json`. Inputs were rebound by `prepare_official_inputs.py`
(49 fixtures, envelopes / scenarios / viewports / oracle expectations byte-identical; only the candidate identity
changed).

## The proposal

| Piece | What it does |
|---|---|
| `frontend/scripts/section-role-oracle.mjs` | ① **Boundary.** Samples every projected edge of the selected section. Polygon edges come from backend vertices; circle and ellipse edges come from a 32-segment polyline. Front edges are scored one by one: ≥ 75 % of visible samples need cobalt within ±2.5 CSS px. Edges seen through the translucent shell are scored in aggregate (≥ 40 %), because they are dashed and other outlines may cross them. ② **Fill.** In the 70 %-shrunk interior, away from the boundary band, ≥ 50 % of samples must read terracotta and ≤ 5 % cobalt. ③ **Ownership.** ≥ 70 % of all cobalt pixels must lie within 6 px of this boundary. It reuses the locked `phanLoaiSac` + `DAI_SAC_VAI_TRO`. |
| `section-role-oracle.node-test.mjs` | Synthetic frames: policy frame passes. Each of these fails: missing boundary, magenta boundary, one edge missing, cobalt/grey fill, cobalt on another object. Overlay exclusion and the hidden-edge threshold are also tested. 9/9. |
| `section-role-browser-probe.mjs` | Real Chrome. The target is selected from «Phân tích toán học» like a learner. Faults are injected at page start: line/mesh colour swap, fill hook, a wrong click. |

Thresholds were fixed from the unfaulted baseline before any fault was run. Two adjustments happened during baseline
only, each recorded:

1. Hidden edges were moved from per-edge to aggregate scoring. A dashed hidden arc of the ellipse was crossed by the
   cutting plane's grey dashed outline (0/12 on one segment).
2. The probe's boundary fault originally swapped colours only in line programs. Circle and ellipse rims are meshes, so
   that fault did not happen on them; the injection was fixed, not the threshold.

### Measured (final integrated candidate `63faa5af`, clean tree; `verification/role-aware-probe/receipt.json`; the same 6/6 and 30/30 on `6c1befcd`)

| Shape × viewport | Baseline | boundary→terracotta | boundary→magenta | fill→grey | fill hidden | wrong object |
|---|---|---|---|---|---|---|
| polygon (official `cross_section_positive`) 1440 / 390 | PASS / PASS | caught / caught | caught / caught | caught / caught | caught / caught | caught / caught |
| circle (sphere sample) 1440 / 390 | PASS / PASS | caught / caught | caught / caught | caught / caught | caught / caught | caught / caught |
| ellipse (replayed p6 cylinder cut) 1440 / 390 | PASS / PASS | caught / caught | caught / caught | caught / caught | caught / caught | caught / caught |

Totals: 6/6 baseline pass, 30/30 faults detected. "Wrong object" is caught twice: by identity (`__geo3d_selected_id`) and
by pixels. Geometry is unchanged in every run.

### Product defect found by the probe — fixed

The ellipse baseline first failed: the front arc of the selected boundary read `(128,115,163)`, which is not cobalt. Root
cause: `scene3d-view.tsx` built the ellipse rim band along `tangent × normal` using the envelope's `normal`. The served
p6 frame is left-handed (`major × minor · normal = −11520`), so the band was built outside the curve. A probe variant
with only `minor_dir` negated passed everywhere, which confirmed the cause. Fix (`3117d513`): band normal =
`major_dir × minor_dir`. RED/GREEN test: `scene3d-unified-materials.test.ts` › "ellipse rim band orientation". This is a
presentation fix that affects every ellipse whose envelope frame is left-handed, selected or not.

## Why the proposal may not replace the gate yet (separate-context review)

| # | Weakness | Consequence |
|---|---|---|
| I-3a | Hue *families*, not policy colours. A `#0075DE` rim with a `#FB923C` fill passes. | A wrong palette that stays in the band is not caught. Needs a colour-distance check against the two policy colours. |
| I-3b | A second section with a full cobalt boundary passes while its perimeter is ≤ ~40 % of the target's (ownership share ≥ 0.7). | Two "selected-looking" sections can pass. Needs per-object ownership: no cobalt band on any other section. |
| — | A 25 % gap on one front edge passes (0.75 threshold). | A partly missing boundary can pass. |
| I-4 | `sectionBoundaryWorld` uses the camera position in world frame. Scenes with a display rotation (`quayHienThi`) or a chart metric are in payload frame. | Front/hidden flags can be wrong on such scenes, so the wrong threshold is applied. The three measured cases are unrotated. |
| I-5 | Cone sections use the radial direction from the axis instead of the slanted cone normal. | 14 of 32 hidden flags were wrong on a reviewer probe. |

Also open (product, minor, from the same review): hover paints exactly like selection, so hovering a second section
while one is selected shows two cobalt boundaries. `hoveredSection` is not reset when the scene changes.

## What the Owner can decide

1. Keep the locked gate. Official result stays 7/8, with the documented policy conflict.
2. Authorise a second iteration of the proposal fixing I-3a/I-3b/I-4/I-5 and the gap tolerance. Then a genuinely
   independent reviewer approves the checker diff, and only then is it wired in for section targets (hue gate kept for
   every other target).

The authors did not choose either option.
