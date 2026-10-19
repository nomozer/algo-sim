# Report — `hybrid-architecture-wave1-exact-certificates-planner`

## 1. Executive Summary

- **Verdict:** **`BATCH_B_AND_ARCH_WAVE1_READY_FOR_REVIEW`**
- **Base (`main` = `origin/main` = `ls-remote`):** `f0560449ec36a37afc7a769ebf965171fff283a0`
- **Session B Research Reference (`research/hybrid-next-architecture-gap-audit`):** `4f1d1a4886ae47c452fb533f21faa883918d175d`
- **Active Branch:** `research/hybrid-architecture-wave1-exact-certificates-planner`
- **Product Commits:**
  - `222cd541` — `feat(geometry): exact altitude certificates, witness preservation, and canonical planner phase ordering`
  - `29a7b8c8` — `feat(geometry): harden exact Gram-metric perpendicular certificates and tamper verifier`
  - `681e0473` — `feat(planner): enforce deterministic dependency-aware call ordering`
  - `fd310cd9` (`fd310cd96379e5c9ae37d25b73fcf00d95ebc4ff`) — `fix(geometry): resolve wave 1 independent review findings on certificates and planner` (**final `product_commit_sha`**)
- **Measured System Identity:** `112` files, `tree_hash = 534c726a4379700be0035752f4925d1ee5573e6d2db1718c07053f2e14ab7bfa`
- **Safety Boundaries Unchanged:** `DEFAULT_MODE = LLM_ONLY`, `CACHE_VERSION = 126`, `RESPONSE_CONTRACT = flat`, `ADAPTER_VERSION = "hybrid-preview-adapter/2"`, `HYBRID_PRODUCT_ENABLEMENT = NO-GO`, `ALLOW_LIVE_AI = 0` (`0` live model requests).

---

## 2. Batch B Conditional Storage Cleanup (`BATCH_B_CLEANUP_VERIFIED`)

All three audited Batch B worktree targets passed pre-removal verification (`status --porcelain` empty, `0` unpushed/unique commits unpreserved, `0` active processes, not in the protected 7-worktree keep-list) and were removed via `git worktree remove` without `--force`:

| Target ID | Path | Branch (Preserved) | HEAD SHA | Estimated Bytes | Status |
|---|---|---|---|---:|---|
| **B2** | `.superpowers/worktrees/hybrid-pre-main-hardening` | `research/hybrid-pre-main-hardening` | `6592306d1a48a04068757b8876ba42cfdb29c452` | `1,813,655,007` | `REMOVED` |
| **B3** | `.superpowers/worktrees/hybrid-preview-contract-hardening` | `research/hybrid-preview-contract-hardening` | `90fe44df34057d6a5646f0e2c61da1b3e961fb56` | `1,813,596,655` | `REMOVED` |
| **B4** | `.superpowers/worktrees/extraction-v2-record-correction` | `docs/extraction-v2-record-correction` | `f2b00ed3ec1e333e3b5c18c046ac5beec1f7b6fb` | `1,813,075,859` | `REMOVED` |

- **Drive `D:` Free Space Before Batch B:** `19,207,282,688` bytes (`17.8882 GiB`)
- **Drive `D:` Free Space After Batch B:** `24,862,683,136` bytes (`23.1552 GiB`)
- **Batch B Actual Reclaimed:** `5,655,400,448` bytes (`5.2670 GiB`)
- **Cumulative Reclaimed (A1 `1,813,733,376` + Batch B `5,655,400,448`):** `7,469,133,824` bytes (`6.9562 GiB`)
- **Untracked Receipt & Report:** `.superpowers/post-session-a-cleanup-storage-audit-20261019T020817Z/batch-b-cleanup-receipt.json` and `batch-b-cleanup-report.md`.

---

## 3. Wave 1A — Exact Geometry Certificates (`ISSUE-ARCH-SCENE3D-ALTITUDE-CERTIFICATE-MISSING`)

### 3.1 Architecture & Mathematical Authority

1. **Exact Gram-Metric Certificate Module (`backend/app/simulation/geometry_functions/certificates.py`):**
   - `validate_gram_metric_spd(chart_metric)`: Enforces exact rational $3 \times 3$ symmetry ($G_{ij} == G_{ji}$) and Sylvester's positive-definiteness criterion ($m_1 > 0, m_2 > 0, \det(G) > 0$) using `fractions.Fraction`. Never falls back to Euclidean $I_3$ on malformed or singular metrics.
   - `certify_line_plane_perpendicularity(...)`: Given a candidate segment $AB$ and a target plane/polygon with vertices $P_0, P_1, \dots, P_{k-1}$:
     - Verifies exact endpoint incidence ($A$ or $B$ coincides with a plane vertex or satisfies exact coplanarity $\det(\text{Gram}(u, v, w)) = 0$ while the other endpoint is strictly off-plane with non-zero segment norm $\langle h, h \rangle_G > 0$).
     - Selects two non-collinear in-plane basis vectors $u, v$ ($\det(\text{Gram}(u, v)) > 0$), prioritizing edges incident to the foot vertex when the foot is a polygon vertex, and scanning vertex pairs when $P_1 - P_0$ and $P_{k-1} - P_0$ are collinear.
     - Certifies perpendicularity **if and only if** both exact rational Gram inner products vanish:
       $$\langle h, u \rangle_G = 0 \quad \text{and} \quad \langle h, v \rangle_G = 0.$$
   - `certify_deductive_line_plane_perpendicularity(...)`: Certifies deductive line-plane perpendicularity (`LINE_PERP_TWO_INTERSECTING_LINES_IN_PLANE`) only when two non-parallel in-plane premise lines ($\det(\text{Gram}(d_1, d_2)) > 0$) are each exactly orthogonal to the line ($\langle h, d_1 \rangle_G = 0, \langle h, d_2 \rangle_G = 0$) and the metric is SPD, strictly excluding `goal_call` and any non-premise (`role="prove"`, `negated=True`, `conditional=True`) calls from self-certification.
   - `verify_perpendicular_witness(...)`: Independently re-verifies any attached `segment3.perpendicular_witness` against `scene["objects"]` and `scene["chart_metric"]`, rejecting missing feet, non-incident feet, oblique segments, collinear plane bases, and non-SPD metrics fail-closed.
   - `attach_scene_perpendicular_certificates(scene, trace=..., chart_metric=...)`: Attaches `perpendicular_witness` to every `segment3` with verified provenance and exact Gram orthogonality to the base face (`CONSTRUCT_BASE` or `solid.faces[0]` fallback), covering right altitudes (`SA`, `SO`, `SH`) and right prism lateral edges (`AA'`, `BB'`, `CC'`, `DD'`) across both Euclidean and oblique Gram charts (`H03`, `H14`) without name/label heuristics.

2. **Default-Route (`Path A`) Segment3 Certificate Emission (`backend/app/simulation/semantic_program/quantity_annotations.py` & `scene3d.py`):**
   - `quantity_annotations._gan_chung_chi_vuong_goc_doan` attaches `perpendicular_witness` (`exact-gram-line-plane-orthogonality/1`) directly to `segment3` objects carrying `CONSTRUCT_HEIGHT` (or `CONSTRUCT_LATERAL_BOUNDARY` on `PRISM_LIKE` solids) when exact Gram inner products `_m.dot(v, u) == 0` and `_m.dot(v, w) == 0` hold, without importing `_ROUTE_D` (`geometry_functions`).
   - `scene3d.py` includes `"perpendicular_witness"` in `_TRUONG["segment3"]` so `build_scene3d` preserves certified `segment3.perpendicular_witness` on Path A (`S1_side_height_volume` `SO`), while `_bam_doan_da_dung` keeps `"witness" not in quantity.annotation` so coinciding segments do not duplicate dashed witness lines.

3. **Frontend Point-vs-Segment Witness Guard (`frontend/src/simulations/domains/geometry/scene3d-annotations.ts`):**
   - Added `o.type === "point3"` before pushing point-projection dashed witness entries (`nhan_chung:${o.id}`), so `segment3.perpendicular_witness` feeds the right-angle marker in `scene3d-view.tsx` without duplicating dashed projection lines or measurement pills.

4. **Test & Fixture Verification (`10/10` Backend Pytest Functions + `34/34` Frontend + `41/41` Adapter `/2` Fixtures):**
   - `backend/tests/geometry/test_hybrid_wave1_exact_certificates.py`: `10/10` pytest functions passing, covering all `12` served Hybrid fixtures (`17` certified perpendicular segments across `H01`–`H12`, `24/24` oblique segments rejected), Path A `S1_side_height_volume` (`SO`) and `N2` non-regular rejection, `square_pyramid_envelope.json` (`chieu_cao_SA`), deductive perpendicularity (`H07` `BC ⊥ (SAB)` + non-self-certification check), and `8` tamper/negative vectors.

---

## 4. Wave 1B — Dependency-Aware Planner Ordering (`GAP-C1` / `ISSUE-RESEARCH-HYBRID-AUXILIARY-BEFORE-SOLID`)

### 4.1 Explicit Dependency Graph & Tiered Topological Sort

Implemented `_sap_xep_phu_thuoc_loi_goi(k: KeHoach)` in `backend/app/simulation/geometry_functions/planner.py`:
- **Root-Solid vs Derived Composite Sub-Solid Classification:** Solids whose vertices have zero overlap with explicit point-producer outputs (`raw_point_outputs`) are classified as `root_solids` (`Tier 0`), while derived composite sub-solids (`M.ABC` in `COMP1` or `M.ABCD` where `M = midpoint(S, C)`) depend on their vertex producers and execute in `Tier 4` before `ask_volume(M.ABC)` in `Tier 5`.
- **Tier Classification (`tier_of` in `_sap_xep_phu_thuoc_loi_goi`):**
  - `Tier 0`: Root solid declarations (`pyramid`, `regular_pyramid`, `prism`, `cuboid`, `cube`)
  - `Tier 1`: Base foundation (`regular_polygon`, `rectangle`, `right_angle`, base `segment_length`, base `equal_length`)
  - `Tier 2`: Apex-foot point constructors (derived points consumed by `Tier 3` apex projection/altitude calls, such as `H = midpoint(AB)` in `H12` when `SH ⊥ (ABC)`)
  - `Tier 3`: Apex & solid metric/perpendicularity premises (`altitude`, `perpendicular_line_plane`, `face_perpendicular_base`, apex `orthogonal_projection`, apex `segment_length`)
  - `Tier 4`: Post-solid auxiliary constructions and derived composite sub-solids (`midpoint`, `centroid`, `translate_point`, `intersect_*`, `intersection_line`, `section`, `perpendicular_lines`, derived `solid`)
  - `Tier 5`: Queries & escapes (`ask_*`, `unsupported`)
- **Explicit Dependency Edges & Fail-Closed Validation:**
  - Validates that every `line_ref` (`UNKNOWN_DERIVED_REFERENCE`), every referenced `solid` (`UNKNOWN_SOLID`), every `depends_on` target (`DANGLING_DEPENDENCY`), and every undeclared point operand (`UNDERDETERMINED_POINT` in `engine.py::giai_phu_thuoc`) is rejected fail-closed.
  - Detects goal-reachable cycles in `direct_deps` and refuses fail-closed with `DEPENDENCY_CYCLE`, while preserving Route A / Route B parity (`UNDERDETERMINED_POINT`) on unreferenced dead point cycles.
  - Preserves `k.calls` in its exact original order whenever no prerequisite edge is violated (preserving all `41/41` committed Adapter `/2` fixtures, including `served-H12_PROJECTION_MIDPOINT_ANGLE`), and otherwise reorders deterministically via min-heap Kahn topological sort keyed by `(tier, original_index, call_id)`.

### 4.2 RED $\to$ GREEN Verification (`10/10` Passed)

- **RED Receipt (before `_sap_xep_phu_thuoc_loi_goi`):** `4 failed, 6 passed` in `backend/tests/geometry/test_hybrid_wave1_dependency_planner.py`.
- **GREEN Receipt (at `fd310cd9`):** `10/10 passed` in `backend/tests/geometry/test_hybrid_wave1_dependency_planner.py`, and `417/417 passed` across the 8 targeted backend geometry test suites (`test_hybrid_wave1_exact_certificates.py` `10`, `test_hybrid_wave1_dependency_planner.py` `10`, `test_hybrid_preview_contract.py` `64`, `test_hybrid_backend_integration.py` `52`, `test_hybrid_compiler_selection.py` `107`, `test_geometry_library_expansion.py` `91`, `test_regular_square_pyramid_height.py` `20`, `test_structured_geometry_relations.py` `63`).

---

## 5. Independent Review & Authoritative Full T3 Verification (`P7`)

- **Independent Mathematical & Architecture Review (`review.md`):** **`INDEPENDENT_REVIEW_PASS`** (`0` Blockers, `0` Important findings after resolving Round 1 findings in `fd310cd9`).
- **Candidate Freeze (`77b05def59d5d39ec1a1e5100f06bab13b4cdd8e`):** `112` measured files, `tree_hash = 534c726a4379700be0035752f4925d1ee5573e6d2db1718c07053f2e14ab7bfa`, `product_commit_sha = fd310cd96379e5c9ae37d25b73fcf00d95ebc4ff` (`freeze_evaluation_candidate.py --verify` MATCH).
- **Authoritative Full T3 Gate (`authoritative-t3.json`, clean detached worktree at `77b05def`):** **`FULL_PRODUCT_GATE_PASS`** (`487.1s` total):
  - Backend Pytest: `10,970 passed, 1 skipped, 2 deselected, 9 xfailed, 0 failed` (`470.7s`)
  - Frontend Vitest: `70 passed (70)` test files, `1,146 passed (1,146)` tests (`8.9s`)
  - Frontend Typecheck + Production Build (`tsc -b && vite build`): `PASS` (`6.1s`)
  - Thesis Demo Replay: `5/5` (`DEMO_REPLAY_PASS`), `1/1` (`REDUCED_CHAIN_CASES`) (`0.9s`)
  - Demo Crash Surface: `6/6` expected boundaries, `0` unhandled 500s (`0.6s`)
- **Temporary Detached Worktree Cleanup:** Removed junction `frontend\node_modules` via `cmd /c rmdir` and unregistered `t3-verify-wave1` via `git worktree remove` without `--force`.

