# Plan — `hybrid-architecture-wave1-exact-certificates-planner`

## 1. Scope & Authorization

- **Authorization:** `GO_BATCH_B_CONDITIONAL_CLEANUP_AND_HYBRID_WAVE1_IMPLEMENTATION`
- **Base (`main` = `origin/main` = `ls-remote`):** `f0560449ec36a37afc7a769ebf965171fff283a0`
- **Session B Research Baseline (`research/hybrid-next-architecture-gap-audit`):** `4f1d1a4886ae47c452fb533f21faa883918d175d`
- **Active Branch / Worktree:** `research/hybrid-architecture-wave1-exact-certificates-planner` at `.superpowers/worktrees/hybrid-architecture-wave1-exact-certificates-planner`

---

## 2. Phases

1. **P0–P2 — One-Batch Conditional Cleanup (Batch B: B2, B3, B4):**
   - Inspect and remove eligible worktrees `B2` (`hybrid-pre-main-hardening`), `B3` (`hybrid-preview-contract-hardening`), and `B4` (`extraction-v2-record-correction`) via `git worktree remove` without `--force`, preserving local branches and tracking receipts in `.superpowers/post-session-a-cleanup-storage-audit-20261019T020817Z/batch-b-cleanup-receipt.json`.
2. **P3 — Isolated Hybrid Architecture Wave 1 Worktree:**
   - Branch `research/hybrid-architecture-wave1-exact-certificates-planner` from `main` (`f0560449`).
3. **P4 — Wave 1A: Exact Geometry Certificates (`ISSUE-ARCH-SCENE3D-ALTITUDE-CERTIFICATE-MISSING`):**
   - Implement exact `Fraction` Gram-metric perpendicularity certification (`backend/app/simulation/geometry_functions/certificates.py`) with Sylvester SPD metric validation, non-collinear plane basis selection, exact `dot(h, u) == 0` and `dot(h, v) == 0` checks, deductive theorem certification (`LINE_PERP_TWO_INTERSECTING_LINES_IN_PLANE`), and tamper verification (`verify_perpendicular_witness`).
   - Preserve `witness` when merging coinciding segment annotations in `backend/app/simulation/semantic_program/quantity_annotations.py::_bam_doan_da_dung`.
   - Guard `frontend/src/simulations/domains/geometry/scene3d-annotations.ts` (`o.type === "point3"`) so `segment3` altitude witnesses are rendered by `scene3d-view.tsx` right-angle markers without duplicating dashed projection lines.
   - Keep `ADAPTER_VERSION = "hybrid-preview-adapter/2"` unchanged and verify additive `segment3.perpendicular_witness` entries in `export_hybrid_preview_fixtures.py --verify`.
4. **P5 — Wave 1B: Dependency-Aware Planner Ordering (`GAP-C1` / `ISSUE-RESEARCH-HYBRID-AUXILIARY-BEFORE-SOLID`):**
   - Replace naive phase sorting in `backend/app/simulation/geometry_functions/planner.py` with `_sap_xep_phu_thuoc_loi_goi`:
     - Build explicit directed dependency edges across producers and consumers (`direct_deps` + `ordering_deps` across `Tier 0` solid declarations $\to$ `Tier 1` base foundation $\to$ `Tier 2` apex-foot point constructors $\to$ `Tier 3` apex/solid metric & perpendicularity premises $\to$ `Tier 4` post-solid auxiliary constructions $\to$ `Tier 5` `ask_*` / `unsupported` queries).
     - Fail closed on dangling references (`DANGLING_DEPENDENCY` / `UNKNOWN_DERIVED_REFERENCE` / `UNKNOWN_SOLID`) and dependency cycles (`DEPENDENCY_CYCLE`) on all plans.
     - Preserve original order when no prerequisite edge is violated (preserving all 41 committed Adapter `/2` fixtures, including `H12`), and reorder deterministically via min-heap Kahn topological sort when out-of-order.
5. **P6–P8 — Regression, Review, Candidate Refreeze, Authoritative Full T3 & Handoff:**
   - Run backend and frontend regression suites, independent code review, candidate refreeze, and clean detached Authoritative Full T3.
