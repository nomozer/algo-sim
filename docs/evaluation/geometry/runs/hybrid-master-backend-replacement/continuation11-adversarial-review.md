# Independent Adversarial Review — Continuation 11 (`ALGOSIM_MASTER_HYBRID_BACKEND_REPLACEMENT`)

- **Reviewer subagent**: `Independent Continuation 11 Adversarial Reviewer` (`76cc54fa-371c-4f90-80a2-36b259724296`, read-only `research` sandbox)
- **Scope audited**: Semantic shape-kind invariant certification (`PE-2`), unanswered request completeness audit (`PE-1` / `SL-1` / `SL-2`), generalized `Point` descriptor & plane-through-described-point planner recomposition, independent finite-horizon `planning_oracle.py`, isolated `S-1` diacritic-free normalization prototype (`s1_diacritic_offline.py`), isolated `S-2` student-language pilot scorer (`score_s2_student_language_pilot.py`), locked provider/schema surface invariants, and historical evidence integrity.
- **Final Verdict**: **`VERDICT: READY`** (`0 BLOCKER, 0 MAJOR, 0 MINOR`; `1` expected pre-freeze `NIT-R3-1` resolved upon candidate freeze)

---

## 1. Review Trajectory Across Four Rounds

| Round | Verdict | Counts | Key Findings & Disposition |
| :--- | :--- | :--- | :--- |
| **Round 1** | `NOT_READY` | `4 BLOCKER, 3 MAJOR, 1 MINOR, 1 NIT` | All 9 findings fixed with dedicated `RED → GREEN` tests (`BLOCKER-1..4`, `MAJOR-1..3`, `MINOR-1`, `NIT-1`) plus right-prism duplicate IR variable guard in `engine.py`. |
| **Round 2** | `NOT_READY` | `3 BLOCKER, 1 MAJOR, 1 MINOR` | All 5 findings fixed (`BLOCKER-R2-1`, `BLOCKER-R2-2`, `BLOCKER-R2-3`, `MAJOR-R2-1`, `MINOR-R2-1`) and verified across 17 regression & new test suites. |
| **Round 3** | **`READY`** | `0 BLOCKER, 0 MAJOR, 1 MINOR, 1 NIT` | All 11 audit vectors `PASS`; all Round 2 findings independently re-verified `FIXED` (`778 passed, 9 xfailed`). Non-blocking `MINOR-R3-1` noted on 3+ solid coordination & post-nominal solid modifiers in `_day_khoi_cho_menh_de`. |
| **Round 4** | **`READY`** | **`0 BLOCKER, 0 MAJOR, 0 MINOR, 1 NIT`** | Delta verification of `MINOR-R3-1` fix (`registry.py:3602-3622` + `test_route_d_semantic_shape_invariants.py:1282-1300`, `41/41 passed`) confirmed `FIXED` (`NIT-R3-1` is the standard post-commit `freeze_evaluation_candidate.py` step). |

---

## 2. Detailed Summary of Findings Closed

### Round 1 Findings (All `FIXED`)

1. **`BLOCKER-1` — Multi-solid & blanket-quote base ownership for unlabelled `"đáy là <shape>"` (`registry.py`)**:
   - Replaced blind single-solid fallback with sentence-aware prose ownership (`_day_khoi_cho_menh_de`) and `ambiguous_base` fail-closed refusal (`AMBIGUOUS_REFERENCE`) when multiple incompatible bases are in scope.
2. **`BLOCKER-2` — Cross-solid & cyclic-order vertex invariants (`engine.py`)**:
   - Verified 2D/3D shape assertions over arbitrary valid solid/sub-solid vertices in exact `Fraction` Gram arithmetic (consecutive polygon edge vectors `v_{i+1} - v_i` preventing bow-tie / self-intersecting quadrilateral permutations, exact right-prism lateral orthogonality and congruence, regular pyramid apex-to-vertex equality, regular hexagon 6-side congruence + parallel opposite pairs + interior cosine $-1/2$).
3. **`BLOCKER-3` — Self-referential / uncertified `Point` descriptors on pre-placed points (`engine.py`, `planner.py`)**:
   - Hardened `_MO_TA` Gram/affine postcondition verifiers (`ENGINE_SELF_CHECK_FAILED` on lying contracts, degenerate lines/planes, or collinear plane triples) and added explicit cycle/self-reference rejection in `_EffectResolver.point`.
4. **`BLOCKER-4` — Multi-word solid-class phrases & unlabelled tetrahedron assertions (`registry.py`, `engine.py`)**:
   - Extended `doc_khang_dinh_loai_hinh` and `kiem_khang_dinh_loai_hinh` to cover `"tứ diện đều"`, `"hình hộp đứng"`, `"hình hộp chữ nhật"`, `"hình lăng trụ đều"`, `"hình lăng trụ xiên"` (`oblique_prism` rejecting lateral edge $\perp$ base), `"tam giác vuông cân"`, `"hình thang cân"`, `"hình thang vuông"` (`at` vertex pair), and side-length modifiers (`cạnh 2a`).
5. **`MAJOR-1` — Planner `MAT_VUONG_DUONG` anchor selection on derived lines (`planner.py`)**:
   - Generalized `_chon_moc_vuong_duong` beyond raw solid skeleton edges to constructcertified perpendicular anchors across derived points, `right_angle` facts, and line-perpendicular-plane relations.
6. **`MAJOR-2` — Independent Planning Oracle separation (`backend/scripts/planning_oracle.py`)**:
   - Verified zero imports from `planner.py`, pure Registry contract enumeration + Exact Kernel execution + independent Gram postcondition verification, and explicit `NOT_ESTABLISHED` reporting beyond `ORACLE_STEP_LIMIT`.
7. **`MAJOR-3` — `S-1` polysemy & raw-quote span safety (`backend/scripts/s1_diacritic_offline.py`)**:
   - Preserved 1-to-1 `norm_char_to_raw_span` mapping, rejected forged normalized quotes (`FORGED_NORMALIZED_QUOTE`), and flagged polysemous ASCII tokens (`goc`, `day`, `tam`, `canh`, `duong`) and lowercase solid notations (`s.abcd`) as `NEEDS_CLARIFICATION`.
8. **`MINOR-1` & `NIT-1` — `S-2` pilot scorer missing/unrecoverable distinction & preview telemetry exposure**:
   - Preserved `NOT_MEASURED` / `NOT_RECOVERABLE` / `UNKNOWN` without coercing to `0` (`score_s2_student_language_pilot.py`) and exported `search_telemetry` cleanly on `route_d.planner`.

### Round 2 & Round 3 Findings (All `FIXED`)

1. **`BLOCKER-R2-1` — Prose solid-symbol matching & secondary sub-solid base attribution (`registry.py`)**:
   - Added `_khop_ky_hieu_khoi` enforcing ordered apex/base (`S.ABC` vs `A.SBC`) and lateral-edge (`ABCD.A'B'C'D'`) correspondence across `_lien_ket_cau`, `_so_dinh_cau_khop`, `_cua_khop`, `_loai_cum_dung`, and `doc_khang_dinh_loai_hinh`, and removed the `len(khoi_calls) == 1` shortcut in `_day_khoi_cho_menh_de` so `"Xét hình chóp D.ABB'A' có đáy là hình vuông"` on cube/cuboid `ABCD.A'B'C'D'` binds to `(A, B, B', A')` and deterministically refuses `INCONSISTENT_FACTS` when `AA' != AB`.
2. **`BLOCKER-R2-2` — Pre-placed point non-degeneracy & collinear projection planes (`engine.py`)**:
   - Added collinearity check (`COLLINEAR_POINTS`) on `mp` in `_mot_buoc` before projection and added positive squared-length / non-zero cross-product / non-zero distance guards across all pre-placed branches of `_dung_khong` (`right_angle`, `perpendicular_line_plane`, `midpoint`, `centroid`, `divide_segment`, `perpendicular_lines`, `face_perpendicular_base`).
3. **`BLOCKER-R2-3` — Benchmark refusal taxonomy & historical gold delta accounting (`hybrid_compiler_benchmark.py`, `test_nlu_extraction_evaluation.py`)**:
   - Classified `"DEGENERATE_POINTS": "contradictory"` in `REFUSAL_CLASS` and recorded `D02`, `D06`, `D07` (`dev` split only; `0` `locked` changes) in `results/historical-gold-delta.json` without mutating frozen receipts.
4. **`MAJOR-R2-1` — Cross-layer derived-line perpendicular anchors via 2D `carrier_planes` (`planner.py`)**:
   - Generalized `_chon_moc_vuong_duong` to propagate point membership across 2D `carrier_planes` to fixed point (`midpoint`, `divide_segment`, `centroid`, `orthogonal_projection_line`, `intersect_line_line`) and select non-coplanar perpendicular pairs spanning $\mathbb{R}^3$ with `d` (verified on pyramid and prism lateral-face centroids).
5. **`MINOR-R2-1` — Mixed-IME diacritic detection (`backend/scripts/s1_diacritic_offline.py`)**:
   - Added `_MISSING_DIACRITIC_CUES` + `_ascii_fold` so partially accented / mixed-IME student inputs still undergo polysemy detection (`NEEDS_CLARIFICATION`) or unambiguous phrase restoration while preserving already-accented words and raw-source spans, and keeping fully accented Vietnamese (`trong`, `tam giác`, `cho`) as `PASSTHROUGH_HAS_DIACRITICS`.
6. **`MINOR-R3-1` — 3+ coordinated solids & post-nominal solid modifiers in `_day_khoi_cho_menh_de` (`registry.py`)**:
   - Walked backwards across the entire consecutive coordinated solid chain (`while i > 0 and coord_rx.fullmatch(...)`) and allowed post-nominal solid modifiers (`đứng`/`đều`/`xiên`/`chữ nhật`) before `(có|với)? chung?` (`41/41` in `test_route_d_semantic_shape_invariants.py`).

---

## 3. eleven-Vector Final Audit Matrix

| # | Audit Vector | Round 4 Final Status |
| ---: | :--- | :--- |
| 1 | Source Gate prose ownership & multi-solid topology binding (`registry.py`) | **`PASS`** |
| 2 | Exact `Fraction` Gram 2D & 3D shape-kind invariant certification (`engine.py`) | **`PASS`** |
| 3 | Engine self-check & pre-placed non-degeneracy (`engine.py`) | **`PASS`** |
| 4 | Generalized planner recomposition & 2D carrier-plane perpendicular anchors (`planner.py`) | **`PASS`** |
| 5 | Independent planning oracle & 24-case matrix parity (`planning_oracle.py`) | **`PASS`** |
| 6 | Isolated `S-1` offline diacritic normalization & mixed-IME safety (`s1_diacritic_offline.py`) | **`PASS`** |
| 7 | Isolated `S-2` student-language pilot scorer & budget/stop gates (`score_s2_student_language_pilot.py`) | **`PASS`** |
| 8 | Hybrid preview contract & Route D `search_telemetry` envelope (`function_route.py`, `hybrid_preview.py`) | **`PASS`** |
| 9 | Production defaults (`LLM_ONLY`, `CACHE_VERSION = 131`, `ALLOW_LIVE_AI = 0`, locked schema SHAs, `0` `frontend/` diff) | **`PASS`** |
| 10 | Historical evidence immutability & append-only `historical-gold-delta.json` | **`PASS`** |
| 11 | Repository-wide geometry regression suite health (`0` unexpected failures) | **`PASS`** |
