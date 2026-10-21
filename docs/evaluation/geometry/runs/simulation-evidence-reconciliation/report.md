# Simulation evidence reconciliation — conditional integration blocked

Date: 2026-10-21. Authorization: `GO_MAIN_SIMULATION_COVERAGE_CONDITIONAL`.

**SIMULATION_GO_MAIN_BLOCKED** · **SIMULATION_EVIDENCE_RECONCILIATION_BLOCKED**

This is a correction/addendum to the original campaign report, capability matrix and independent-review artifact descriptions. Original reports, fixtures, screenshots, receipts, oracles and raw logs remain unchanged. This run and the evidence-index correction are local, uncommitted documentation. No new geometric feature, test source, script, candidate metadata, or routing change was made.

The original logs support the recorded test outcomes in the original worktree. The blocker concerns preservation and verification of their exact raw bytes through Git, not an assertion that the tests failed.

## Git and measured identities

- Main, origin/main and directly checked remote main: `bd8d6a9dc3acc9a4204b616379001270bb6d39f9`.
- Source HEAD: `d86c72031d8fc85cd4eef62d9379cd1690ba1417`; root checkout stays on Wave 3A at `fe9f555437498432427ae6bbd54402cdd59c7eb7`.
- Product: `3298b901d2246650535aa4028845ddc2a44892c4`.
- Candidate freeze / authoritative Full T3 target: `5f4ee58c48011e9e5d38d3209f7c97250032a976`.
- Measured system: `4d11a91790422b9508bc90921f4352687a4b8616c0f855886e76649d3a7dcf68`, 114 files; freeze **MATCH**, independently reproduced in a clean detached source checkout.
- Main -> product -> candidate -> source ancestry is valid. Product files equal the candidate; candidate -> source changes are documentation/receipts/logs only. Backend/frontend tests, scripts and candidate metadata have no delta.
- Independent review Round 2 names the exact final product and measured hash. Its artifact and scope claims still require the corrections below.

## Blocking raw-log identity discrepancy

`core.autocrlf=true`; no text/eol override applies to the log paths. Both stdout originals contain mixed CRLF and LF. Removing CR in CRLF explains their committed Git bytes exactly. A clean checkout converts the Git text to CRLF throughout. These are three different raw identities; a normalized comparison cannot silently replace a raw hash.

| Log | Recorded/source raw SHA256 | Git blob SHA256 | Clean detached SHA256 |
|---|---|---|---|
| `attempt1-fail.stdout.log` | `e2074c0897550bda185a6f55ea4113e3a8324263fc7a0cf1e2743228207c03f6` | `2620186c4513cb7a9935f83de6397f5aa03fa38e2de4206ece553391701988e4` | `bf5afed87bfbb445255af70305ddad7a98ad1d13feb86ddc56b97c9022af3e63` |
| `attempt1-fail.stderr.log` | `bfd6d2ca0bf9c3f05bf6010dd12a9c949656172434d9579ba24fdc3701be54a5` | `bfd6d2ca0bf9c3f05bf6010dd12a9c949656172434d9579ba24fdc3701be54a5` | `b24b50561fb68fa16789abd6199d9006687985233ac9814702d9d0206d2b3e43` |
| `attempt2-pass.stdout.log` | `013f2e784e9fa828a055320468afe7137f080d2447615aec3c3d3970a2138e06` | `8274c4c26793ea001f892ee9c90f339f7fdeb93a43b5c92f3c8e409ca547ae6b` | `032b8253c23fbc160a0d7493d8403e502c07a9274ee88a2cbb30629f990e2eba` |
| `attempt2-pass.stderr.log` | `47de58275e7e069019a5f60938442317568919cd55fcaf2c0cd567fee13589c0` | `47de58275e7e069019a5f60938442317568919cd55fcaf2c0cd567fee13589c0` | `befd638b3457a68859fad12c82897daba8b1746520f9fb82289a5635383c5279` |

All four source originals match their recorded hashes. Neither stdout Git blob matches its receipt. None of the four files in the clean detached checkout matches its raw receipt hash. The matching original bytes still exist in the source worktree: retain it. Do not remove it based only on `git status` cleanliness; Git treats these normalized text variants as clean.

Original stdout was read and checked directly: backend 11,439 passed (1 skipped, 2 deselected, 9 xfailed), frontend 72 files / 1,154 passed, production typecheck/build PASS, thesis replay 5/5 (reduced chain 1/1), crash boundary 6/6 with zero escaped 500, final FULL_PRODUCT_GATE_PASS. Receipt exit code is 0. Both attempts and all four raw-log hashes are audited in `evidence.json`.

## Authoritative demo matrix

Authority is the frozen candidate Git tree, not either narrative inventory. All nine envelope route_d.scene3d values exactly equal the corresponding browser-input scenes. All IDs match the saved receipt. All 49 receipt-referenced PNGs exist and equal their frozen Git blobs. Full per-file screenshot paths and SHA256 values are in `evidence.json`.

Paths below are relative to the original campaign `demos/` directory. Hashes are SHA256 of exact **Git blob bytes** at the frozen candidate. Worktree JSON uses CRLF and has separate raw hashes in the machine audit.

| Demo path | Blob SHA256 | Actual geometry scenario | Expected objects | Browser receipt | Screenshots | Execution status |
|---|---|---|---|---|---|---|
| `demo1-pyramid-derived-section.json` | `47c4dfa7575beb60c5f9e993b277c681e83e973d04c621e927d486cbf8b13c3f` | Square-base right pyramid S.ABCD, SA=2 at base vertex A; parallel mid-height section MI1I2I3, area 1, upper-pyramid volume ratio 1/8 | Parent and upper pyramid meshes; section; cutting plane; derived I1/I2/I3; no residual mesh | `visual-acceptance-receipt.json` result `demo1-pyramid-derived-section` | 6: default, orbit, selected, exploded, step0, explorer | RECEIPT_RECORDED_SERVED |
| `demo2-unnamed-section-intersections.json` | `052e37205a6c4c85e17ead6e25096f62fa0f3cc1722a14fcaf46b89c5759132a` | Rectangle-base right pyramid, AB=2 BC=4 SA=3; SM/SA=1/3; parallel section MI1I2I3, area 8/9; residual volume 208/27 | Parent and upper pyramid meshes; section; cutting plane; derived intersections; scalar residual only | `visual-acceptance-receipt.json` result `demo2-unnamed-section-intersections` | 6: default, orbit, selected, exploded, step0, explorer | RECEIPT_RECORDED_SERVED |
| `demo3-multi-solid-shared-geometry.json` | `7c453812de25f42a5f5fa61b22233df88c2b9178d4035beba506e2cbf01b7f78` | Two triangular pyramids S.ABC and D(pyr2).ABC sharing ABC; qualified D identities; volumes 4 and 4/3 | Two pyramid meshes, shared base polygon, separate D and D1 point identities; no prism/cube | `visual-acceptance-receipt.json` result `demo3-multi-solid-shared-geometry` | 6: default, orbit, selected, exploded, step0, explorer | RECEIPT_RECORDED_SERVED |
| `demo4-step-by-step-construction.json` | `8615ae838be116933d2aa92ccb2dc4e43c205a665ddaf536b6327d7d4f6f184f` | Right triangular pyramid S.ABC, AB=3 AC=4 SA=3; midpoint M and perpendicular section through M; construction playback | One parent pyramid mesh, triangular section, cutting plane, derived I1/I2; no centroid | `visual-acceptance-receipt.json` result `demo4-step-by-step-construction` | 6: default, orbit, selected, exploded, step0, explorer | RECEIPT_RECORDED_SERVED |
| `demo5-selection-and-highlighting.json` | `dc8c780abd19325cd3f7dd4e00f90d25945b6885d72e886dbdb294820cb800f4` | Two square-base pyramids S.ABCD and T.ABCD sharing ABCD; heights 2 and 4; parallel section in first pyramid; ratio 1/2 | Two pyramid meshes, shared base, section and derived intersections; no prism | `visual-acceptance-receipt.json` result `demo5-selection-and-highlighting` | 6: default, orbit, selected, exploded, step0, explorer | RECEIPT_RECORDED_SERVED |
| `demo6a-curved-cylinder-sections.json` | `89bded678b1fb7589ecabfa4895d6c11cdb42197048806d0eb34521c8a485581` | Right circular cylinder R=2 h=3; circular cut z=1 and axial rectangular section | Cylinder mesh; base/top/section circle3; axial polygon3; axis and generators | `visual-acceptance-receipt.json` result `demo6a-curved-cylinder-sections` | 6: default, orbit, selected, exploded, step0, explorer | RECEIPT_RECORDED_SERVED |
| `demo6b-curved-cone-frustum-cut.json` | `fda86ad1799e2b8ad7b02a7f8757372a74fd29f5a9b10e5d79887b5b7d4fb735` | Right circular cone R=3 h=4; parallel cut z=2; axial triangle; upper-cone ratio 1/8; residual volume 21pi/2 | Parent and upper cone meshes; base/cut circle3; axial polygon3; planes; scalar residual, no frustum mesh | `visual-acceptance-receipt.json` result `demo6b-curved-cone-frustum-cut` | 6: default, orbit, selected, exploded, step0, explorer | RECEIPT_RECORDED_SERVED |
| `demo6c-curved-sphere-plane-cut.json` | `ea06b12896c6291329c231302833870e6a6a98ce3d2a485854ee9b618faeb68e` | Sphere R=5; plane z=3; section circle radius 4 | Sphere mesh, circle3 section, plane3, exact scalar certificates | `visual-acceptance-receipt.json` result `demo6c-curved-sphere-plane-cut` | 6: default, orbit, selected, exploded, step0, explorer | RECEIPT_RECORDED_SERVED |
| `demo7-invalid-geometry-safe-refusal.json` | `bb462747338c7e0a21bb38a90116dffc6f14b8a3c0e5d3ecacb524d77e9948ba` | Sphere R=5; plane z=7 outside sphere | REFUSED CURVED_PLANE_DOES_NOT_CUT; null scene3d; refusal UI | `visual-acceptance-receipt.json` result `demo7-invalid-geometry-safe-refusal` | 1: refused | RECEIPT_RECORDED_REFUSED |

**Counts:** browser 8 served + 1 refused = 9; 48 positive PNGs + 1 refusal PNG = 49. Development corpus 10 positive + 5 negative = 15, not 15 browser scenes. All 15 are DEVELOPMENT_EVALUATION_NOT_BLIND, not a blind holdout.

Neither narrative is authoritative: demo1 is a vertex-altitude square-base pyramid with MI1I2I3, not a regular pyramid MNPQ/residual-frustum demo. Demo2 is a parallel section of a rectangle-base pyramid, not an (ABM) cut. Demo3 contains two pyramids, not a cube/prism plus pyramid. Demo4 has no centroid. Demo5 contains two pyramids, not a prism. Demo7 uses z=7 and CURVED_PLANE_DOES_NOT_CUT, not z=6 or TYPED_FACT_NEXT_INCONSISTENT_WITNESS. AMNI1 and a separate cone-ellipse demo are absent from this inventory.

The saved receipt records scenesFile as `demos/browser_demos_scenes.json`; the runner defaults to a different baseline input, so selecting that inventory would require an explicit `--scenes` argument. This reconstructs the required invocation, not an observed original command. The final screenshots are in `screenshots/`. An original browser shell execution log, full command line, execution timestamp, runtime commit/hash and original output arguments are UNKNOWN in the tracked package. No original browser execution log was found in the source run. These cannot be reconstructed as observed facts from the report. No browser rerun was performed after the preflight block.

The baseline and post-P3 receipts also contain zero ellipse3 objects. Neither cylinder nor cone ellipse was browser-tested in any saved receipt in this campaign. The two extra positive development cases are `pos_09_cylinder_oblique_ellipse` and `pos_10_cone_oblique_ellipse`; they supply backend/Scene3D evidence only.

## Scientific scope: five separate levels

| Shape/scenario | A: analytical kernel | B: offline TypedFactNext / Adapter /3 | C: actual Scene3D output | D: saved browser evidence | E: default user-facing route |
|---|---|---|---|---|---|
| Right circular cylinder | CurvedSolid and exact circle/ellipse/volume operations | Implemented, offline | curved_solid, circles, axial polygon; backend ellipse case | demo6a: circle and axial rectangle; no ellipse | No new live natural-language claim validated |
| Right circular cone | Exact finite cone and conic classification | Implemented, offline | Parent cone, upper cone, circles, axial polygon; backend ellipse case | demo6b: parallel circle and axial triangle; no ellipse | No new live natural-language claim validated |
| Sphere | Exact sphere and circular plane intersection | Implemented, offline | ball curved_solid, circle3, plane3 | demo6c valid; demo7 non-cutting refusal | No new live natural-language claim validated |
| Polyhedral frustum | Generic polyhedral kernel exists; a dedicated frustum feature was not established | Reported DerivedSubSolidSpec/frustum_like does not exist; derived-solid compilation emits pyramid | No residual/frustum mesh in the authoritative demos | No such residual mesh tested in this inventory | Unsupported claim must be withdrawn |
| Cone parallel cut / residual | Parent-minus-upper-cone exact volume and direct formula cross-check | Implemented for derived upper cone | Parent cone + upper cone + cut circle/plane + scalar residual | demo6b renders these objects, not a residual frustum mesh | Offline result only |
| Standalone cone_frustum | BLOCKED_BY_KERNEL | Explicit refusal | No scene | Backend negative, no standalone browser demo | Remains blocked |

The missing polyhedral feature is confirmed by runtime schema introspection in the clean detached checkout (DerivedSubSolidSpec absent), absence of `frustum_like` throughout backend/app, and `_compile_derived_solids_and_goals` emitting `fn="pyramid"` with apex + section cycle. Relevant code: `typed_fact_next.py` SimulationGoalSpec and `adapter3_simulation.py` around lines 982–1030. The campaign report/capability matrix claims of a dedicated ABMN.ABCD residual mesh are not supported by this implementation.

Finite conic validity is checked in `curved.py`: cylinder ellipses must remain between both caps; cone `_elip_non` classifies conic type, requires a valid finite nappe and rejects an ellipse crossing the base. Parabola/hyperbola and clipped sections are refused, not relabeled as full ellipses. Cylinder backend fixture R=3 h=20, x-z+10=0 has z in [7,13], within [0,20]. Cone backend fixture R=6 h=8, x-3z+9=0 has extreme heights 4/3 and 4, within [0,8]. These checks support finite geometry, not browser execution. Sphere demo z=3 has d<R and radius 4; z=7 is outside R=5 and has null scene.

OFFLINE_SIMULATION_E2E is distinct from LIVE_NATURAL_LANGUAGE_PRODUCT_E2E. The former uses prepared TypedFactNext payloads; the latter would require independently measured live extraction, source-grounding/coverage and the default product route. No provider was called and no such live claim is made.

## Integration, validation and cleanup disposition

- P0: BLOCKED by raw-log Git identity. P1: artifact inventory reconciled; original browser execution provenance incomplete. P2: scope corrections required; reported polyhedral residual mesh is not implemented.
- Correction-document checks: **4 passed** (evidence paths, acyclic correction chain, unique wave IDs, permitted docs locations), `git diff --check` clean. These validate only the local addendum/index.
- P3 merge: NOT RUN. Main has not advanced. P4 post-main backend/frontend, historical 174, Adapter /2 41, SGH/BH2A/BH2C, Source Gate/Route A, fingerprints, typecheck/build and docs/evidence tests: NOT RUN in this task because pre-merge gates failed. Original T3 is recorded above; it is not a fresh post-main result.
- P5 push: NOT RUN. P6 cleanup: NOT RUN. Source branch and worktree retained. New clean detached verification worktree `../verify-simulation-go-main` at source HEAD retained; root checkout, user-owned/untracked files, unrelated branches/worktrees and Windows permissions unchanged.
- Governance preserved: DEFAULT_MODE=LLM_ONLY, RESPONSE_CONTRACT=flat, HYBRID_PRODUCT_ENABLEMENT=NO-GO, ALLOW_LIVE_AI=0, CACHE_VERSION=127; Adapter /3 research-only; no default /api/analyze route change, live request, Wave 3B or feature work.
- Reused: existing candidate verifier, frozen Git objects, original receipts/runner and geometry code. Created: this correction report, run metadata and machine audit only. No product modules were added; no duplicate implementation.

## Remaining gaps and thesis evaluation

Preserve the matching raw originals and repair their reproducible evidence packaging in an explicitly reviewed correction layer before retrying integration. Do not edit the old hashes to match normalized bytes or overwrite original logs. Browser execution provenance and any future ellipse browser coverage need separately recorded runs. Withdraw residual-mesh claims rather than implement new geometry during this task.

This task does not certify readiness for thesis-level user evaluation. Supervised exploration of the existing offline demonstrations has saved visual evidence, but live natural-language-to-Scene3D coverage, held-out user effectiveness and the claimed residual/frustum mesh remain gaps. No further implementation campaign was started.
