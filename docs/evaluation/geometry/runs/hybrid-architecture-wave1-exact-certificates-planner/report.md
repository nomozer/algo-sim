# Report — `hybrid-architecture-wave1-exact-certificates-planner`

## 1. Executive Summary

- **Verdict:** **`BATCH_B_AND_ARCH_WAVE1_READY_FOR_REVIEW`**
- **Base (`main` = `origin/main` = `ls-remote`):** `f0560449ec36a37afc7a769ebf965171fff283a0`
- **Session B Research Reference (`research/hybrid-next-architecture-gap-audit`):** `4f1d1a4886ae47c452fb533f21faa883918d175d`
- **Active Branch:** `research/hybrid-architecture-wave1-exact-certificates-planner`
- **Product Commits:**
  - `222cd541` — `feat(geometry): exact altitude certificates, witness preservation, and canonical planner phase ordering`
  - `29a7b8c8` — `feat(geometry): harden exact Gram-metric perpendicular certificates and tamper verifier`
  - `681e0473` (`681e047335595acbd091ebcbbc673075f18ca5b0`) — `feat(planner): enforce deterministic dependency-aware call ordering` (**final `product_commit_sha`**)
- **Measured System Identity:** `112` files, `tree_hash = 4c9181bc30e0e511b22ebb25d781d68e3947428986e2838670504350e6eaa263`
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
     - Selects two non-collinear in-plane basis vectors $u, v$ ($\det(\text{Gram}(u, v)) > 0$), prioritizing edges incident to the foot vertex when the foot is a polygon vertex.
     - Certifies perpendicularity **if and only if** both exact rational Gram inner products vanish:
       $$\langle h, u \rangle_G = 0 \quad \text{and} \quad \langle h, v \rangle_G = 0.$$
   - `certify_deductive_line_plane_perpendicularity(...)`: Certifies deductive line-plane perpendicularity (`LINE_PERP_TWO_INTERSECTING_LINES_IN_PLANE`) only when two non-parallel in-plane lines ($\det(\text{Gram}(d_1, d_2)) > 0$) are each exactly orthogonal to the line ($\langle h, d_1 \rangle_G = 0, \langle h, d_2 \rangle_G = 0$) and the metric is SPD.
   - `verify_perpendicular_witness(scene, seg_obj)`: Independently re-verifies any attached `segment3.perpendicular_witness` against `scene["objects"]` and `scene["chart_metric"]`, rejecting missing feet, non-incident feet, oblique segments, collinear plane bases, and non-SPD metrics fail-closed.
   - `attach_scene_perpendicular_certificates(scene)`: Attaches `perpendicular_witness` to every `segment3` orthogonal to the base face (`face_id == "base"` or `id == "mp_day"`), covering right altitudes (`SA`, `SO`, `SH`) and right prism lateral edges (`AA'`, `BB'`, `CC'`, `DD'`) across both Euclidean and oblique Gram charts (`H03`, `H05`, `H11`) without name/label heuristics.

2. **Default-Route Witness Preservation (`backend/app/simulation/semantic_program/quantity_annotations.py`):**
   - In `_bam_doan_da_dung`, when a height/distance annotation with a certified `witness` merges onto an already-constructed `segment3` with identical endpoints (`cung_doan`), the `witness` is preserved on the target segment's annotation (`"witness": d["witness"]`) so `scene3d-view.tsx` renders the right-angle marker on Path A (`w11_rectangular_pyramid`, `square_pyramid_envelope.json`) as well as Path B.

3. **Frontend Point-vs-Segment Witness Guard (`frontend/src/simulations/domains/geometry/scene3d-annotations.ts`):**
   - Added `o.type === "point3"` before pushing point-projection dashed witness entries (`nhan_chung:${o.id}`), so `segment3.perpendicular_witness` feeds the right-angle marker in `scene3d-view.tsx` without duplicating dashed projection lines or measurement pills.

4. **Test & Fixture Verification (`18/18` Backend + `34/34` Frontend + `41/41` Adapter `/2` Fixtures):**
   - `backend/tests/geometry/test_hybrid_wave1_exact_certificates.py`: `18/18` passing, covering all `12` served Hybrid fixtures (`17` certified perpendicular segments across `H01`–`H12`, `24/24` oblique segments rejected), Path A `square_pyramid_envelope.json` (`chieu_cao_SA`), deductive perpendicularity, and `8` tamper/negative vectors (oblique edge labelled `"chiều cao"`, only-1-line perpendicularity, parallel non-intersecting lines, missing foot, off-plane foot, non-SPD metric, collinear basis, tampered marker vector).

---

## 4. Wave 1B — Dependency-Aware Planner Ordering (`GAP-C1` / `ISSUE-RESEARCH-HYBRID-AUXILIARY-BEFORE-SOLID`)

### 4.1 Explicit Dependency Graph & Tiered Topological Sort

Implemented `_sap_xep_phu_thuoc_loi_goi(k: KeHoach)` in `backend/app/simulation/geometry_functions/planner.py`:
- **Tier Classification (`_phan_tang_loi_goi`):**
  - `Tier 0`: Solid declarations (`pyramid`, `regular_pyramid`, `prism`, `cuboid`, `cube`)
  - `Tier 1`: Base foundation (`base_shape`, `base_edge`, `right_angle_at`, `segment_length` on base edges)
  - `Tier 2`: Apex-foot point constructors (derived points consumed by `Tier 3` apex projection/altitude calls, such as `H = midpoint(AB)` in `H12` when `SH ⊥ (ABC)`)
  - `Tier 3`: Apex & solid metric/perpendicularity premises (`altitude`, `lateral_edge`, `perpendicular_line_plane`, apex `orthogonal_projection`, apex `segment_length`)
  - `Tier 4`: Post-solid auxiliary constructions (`midpoint`, `centroid`, `point_on_segment`, `translate_point`, `intersection_*`, `section`, `perpendicular_Line_line`, `perpendicular_planes`)
  - `Tier 5`: Queries & escapes (`ask_*`, `unsupported`)
- **Explicit Dependency Edges & Fail-Closed Validation:**
  - Validates that every `line_ref` (`UNKNOWN_DERIVED_REFERENCE`), every referenced `solid` (`UNKNOWN_SOLID`), and every non-solid point operand (`DANGLING_DEPENDENCY`) is defined before use.
  - Detects cycles in `direct_deps` via Kahn's algorithm and refuses fail-closed with `DEPENDENCY_CYCLE`.
  - Runs on **all** plans (both direct plans and `_EffectResolver` plans).
  - Preserves `k.calls` in its exact original order whenever no prerequisite edge is violated (preserving all `41/41` committed Adapter `/2` fixtures, including `served-H12_PROJECTION_MIDPOINT_ANGLE`), and otherwise reorders deterministically via min-heap Kahn topological sort keyed by `(tier, original_index, call_id)`.

### 4.2 RED $\to$ GREEN Verification (`10/10` Passed)

- **RED Receipt (before `_sap_xep_phu_thuoc_loi_goi`):** `4 failed, 6 passed` in `backend/tests/geometry/test_hybrid_wave1_dependency_planner.py` (out-of-order `midpoint` before `pyramid` when resolver was unused, dangling point reference in `ask_length`, cyclic point dependencies, and `H12` apex-foot ordering).
- **GREEN Receipt (at `681e0473`):** `10/10 passed` in `backend/tests/geometry/test_hybrid_wave1_dependency_planner.py`, covering all 8 required scenarios:
  1. Auxiliary point fact before solid fact $\to$ solid emitted first (`Tier 0` before `Tier 4`).
  2. Multi-step chain (`solid` $\to$ `midpoint M` $\to$ `projection H of M` $\to$ `distance/area/angle ask`) $\to$ topological order.
  3. Two-line parallel plane section (`M` + `translate_point` + `section` + `ask_section_area`) $\to$ solid before auxiliary points before section before ask.
  4. Permuted input facts (`6` permutations) $\to$ identical canonical call sequence and identical exact answers.
  5. Shared auxiliary point across multiple questions $\to$ constructed once before all dependent asks.
  6. Missing/dangling dependency $\to$ fail-closed refusal (`DANGLING_DEPENDENCY` / `UNKNOWN_DERIVED_REFERENCE` / `UNKNOWN_SOLID`).
  7. Cyclic dependency injection $\to$ fail-closed refusal (`DEPENDENCY_CYCLE`).
  8. Existing regression corpus (`174/174` historical + `40/40` Slice A/B + `41/41` Adapter `/2` fixtures) $\to$ `0` answer drift, `0` timeline violations.
