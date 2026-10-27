# handoff.md — `hybrid-v2-adapter4-plane-section-certificate`

- **Status:** `READY_FOR_OWNER_REVIEW`. Not merged, not pushed, no worktree cleanup performed.
- **Branch / worktree:** `research/hybrid-v2-adapter4-plane-section-certificate` · `.superpowers/worktrees/adapter4-plane-section-certificate`.
- **Baseline `main` before:** `a3ee14a707f35dddd70a52f551d23beb16476c41`.
- **New product commit:** `f54c3561b09153021bba0b35a5a9ab78a82546b3` (initial implementation `05f3bd47d294ac034b9965c28dfb4f826640556e` + Adapter `/2` trace compatibility & `NIT-1` fix `f54c3561b09153021bba0b35a5a9ab78a82546b3`).
- **New frozen candidate (T3):** `0be084d95d5343e0c25adeef12c99b5e17811054` (`118` files, `tree_hash = ae6360b1d20beb96b87bad4f335b74b3a61e7483d06214aa2192f17fe6f1c70a`).
- **Full T3:** `FULL_PRODUCT_GATE_PASS` (`12,421 passed, 1 skipped, 2 deselected, 15 xfailed` backend; `83 files / 1,417 passed` frontend; build PASS; demo `5/5` + `1/1`; crash `6/6`; post-T3 freeze `MATCH`, [`full-t3/receipt.json`](full-t3/receipt.json)).
- **Independent Review:** `INDEPENDENT_REVIEW_PASS` (`0 BLOCKER`, `0 MAJOR`, `0 MINOR`, `2 NIT` resolved; [`review.md`](review.md)).
- **Versions:** `registry /17` · `planner /16` · `engine /14` · `Adapter /4` · `CACHE_VERSION = 130` (`NO_BUMP`) · `DEFAULT_MODE = LLM_ONLY` · Hybrid opt-in only · `0` live provider calls.

## Summary of `ADAPTER_INTEGRATION_GAP` Closure (`plane-section-certificate/1`)

1. **Category A vs. Category B Separation ([`architecture-decision.md`](architecture-decision.md)):**
   - **Category A (`DINH_CAT_CANH`):** Source-stated or planner-declared edge cuts (`section_vertex_from_cut` / `dinh_cat_canh`) + `D6` closure certificate (`_validate_category_a_section`).
   - **Category B (`plane-section-certificate/1`):** Engine-derived plane-section certificate (`certificate_category = "ENGINE_DERIVED_SECTION"`, `rule = "engine_derived_plane_section"`, `producer = "engine.kiem_chung_chi_thiet_dien"`) emitted on `KetQuaTuyen.section_certificates` (`engine.py`) and validated in exact `Fraction` arithmetic by `_validate_engine_derived_section` (`adapter4_route.py`) across all 10 mathematical and structural invariants (§4.2).
2. **Development & Tamper Evaluation ([`results/red-before.json`](results/red-before.json) → [`results/green-after.json`](results/green-after.json)):**
   - **Positive cases (`18`):** `1/18` → **`18/18` (`100%` exact Euclidean oracle agreement)** across triangular/quadrangular/oblique prisms, cuboids, cubes, regular/rectangular/right-trapezoid pyramids, `MAT_VUONG_DUONG`, `MAT_SONG_SONG`, `MAT_HAI_DUONG`, simulation-only and area-asked goals, plus Category A control (`P18`).
   - **Negative & Tamper cases (`18`):** `18/18` → **`18/18` (`100%` fail-closed)** across source gate refusals, underdetermined geometry, degenerate/face planes, and 10 certificate tamper vectors (`N09..N18`).
   - **Regression & Tamper Pytest Suite (`test_adapter4_plane_section_certificate.py`):** **`39/39` passed** (including `17` tamper tests covering empty `route_d["sections"]` when `scene3d` has a `section` object, off-plane vertex, invalid edge $t$, non-edge vertex pair, collinear/zero-area polygon, bow-tie non-convex ordering, `area_squared` mismatch vs. `kq_<qid>`, internal label leak, unverified closure certificate, wrong producer, and category mixing).

## Leftovers Preserved Per Authorization

- **Detached T3 checkout:** `D:/Documents/projects/algo-sim/.superpowers/worktrees/.superpowers/worktrees/premerge-red` (currently detached at `0be084d95d5343e0c25adeef12c99b5e17811054`; `frontend/node_modules` and `backend/.venv` are directory junctions — use `rmdir` on the junctions before `git worktree remove` when cleanup is eventually authorized).
- **All existing worktrees:** untouched.

## Decisions for the Owner

1. **GO MAIN** review for `research/hybrid-v2-adapter4-plane-section-certificate` (closing `ADAPTER_INTEGRATION_GAP` for plane-only derived sections on Adapter `/4`).
2. **Subsequent waves after GO MAIN:**
   - Independent Vietnamese holdout evaluation (`INDEPENDENT_HOLDOUT_NOT_EXECUTED`) before any curriculum readiness claim.
