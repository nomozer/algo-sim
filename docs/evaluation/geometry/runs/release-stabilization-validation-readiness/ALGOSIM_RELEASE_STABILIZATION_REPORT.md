# ALGOSIM — RELEASE STABILIZATION, EVIDENCE INTEGRITY & INDEPENDENT VALIDATION READINESS REPORT

- **Run Slug**: `release-stabilization-validation-readiness`
- **Branch**: `feat/release-stabilization-validation-readiness` (forked from `main` at `32f14b8fc4231b6a57ada34966c019e99ff148c0`)
- **Product Commit SHA**: `b8a9e57b4fb13b2ecdba188fbea6f2a76d57caba` (`b8a9e57b4`)
- **Measured System Tree Hash**: `c09b67d538d7d450dc03d8ccaacbb00676241aa4f342d8dbca07bedae974be01` (`so_file = 106` hashed entries across `105` unique measured files)
- **Active Route & Versions**: `Hybrid /4` (`typed-fact-next/2`, `typed-fact-next-bridge/2`, `geometry-fact-planner/26`, `geometry-functions/33`, `geometry-function-engine/24`, `hybrid-simulation-adapter/4`, `CACHE_VERSION = "132"`, `ROUTE_D_CACHE_POLICY = "132:route-d"`)
- **Live AI Budget Enforcement**: `ALLOW_LIVE_AI = 0` (`0` live Gemini API calls executed)
- **Historical Evidence Integrity**: `docs/evaluation/geometry/runs/independent-geometry-and-vision-evaluation/**` (`0` bytes modified; correction layer registered via `CORRECTED_BY`)

---

## A. Evidence Reconciliation

Machine-readable receipt: [`evidence_reconciliation_receipt.json`](evidence_reconciliation_receipt.json) (`SHA-256: dc2254405103...`).

All seven metric discrepancies between historical prose summaries, documentation, and machine receipts have been audited and reconciled against source-of-truth artifacts and code without modifying any frozen historical receipt bytes:

| ID | Discrepancy Surface | Previous Claim / Ambiguity | Authoritative Source & Reconciled Fact | Status |
|---|---|---|---|---|
| **R-1** | `EVALUATION_CANDIDATE.json` file count (`106` vs `105`) | Reports stated either `106` files or `105` files without distinguishing list length from unique paths | `freeze_evaluation_candidate.py::_measured_system_files()` hashes `106` path entries (`so_file = 106`), which resolve to `105` unique file paths because `MEASURED_SYSTEM_PATHS` lists both directory `"frontend/src/simulations/domains/semantic"` and file `"frontend/src/simulations/domains/semantic/semantic_program.schema.json"` (the exact lowercase POSIX path `frontend/src/simulations/domains/semantic/semantic_program.schema.json` appears twice, 100% deterministic across Windows, Linux, and macOS). | `RECONCILED` |
| **R-2** | `test_hybrid_reasoning_generalization.py` counts | Earlier prose (`fb5f9a69`) cited `22 passed, 6 xfailed (28 total)`; post-`32f14b8f` cited `28 passed, 6 xfailed (34 total)` | Commit `32f14b8f` added 6 new positive tests (`IH-B3`, `IH-E2`, `IH-F1`, `IH-F2` + 2 unit tests) to the `22 passed, 6 xfailed` baseline, yielding `28 passed, 6 xfailed (34 total)`. In this release stabilization branch (`b8a9e57b4`), 7 new multi-apex/multi-anchor mathematical tests were added, bringing the suite to **`35 passed, 6 xfailed` (`41` collected items, `0 failed`)**. | `RECONCILED` |
| **R-3** | Held-Out Geometry Evaluation (`46` cases) | Single aggregate score risked conflating direct TypedFactNext replay (`38` cases), oracle FactGraph (`6` cases), and raw Vietnamese text gate (`2` cases) | Explicitly decomposed in `docs/CURRENT_STATE.md` and `evidence_reconciliation_receipt.json`: (1) Total corpus = `46/46 PASS` (`100.0%`); (2) Direct `TypedFactNext -> Source Gate -> FactGraph -> Planner /26 -> Registry /33 -> Exact Kernel /24 -> Adapter /4` (`38` cases: `33 SOLVED_EXACT` + `5 CORRECT_REJECTION`) = **`38/38` (`100.0%`)** (`31/38 = 81.58%` before `32f14b8f` fixes); (3) Oracle `FactGraph -> Planner /26 -> Exact Kernel /24` (`6` cases `G1/G5/G8`) = **`6/6` (`100.0%`)**; (4) Raw Vietnamese out-of-scope gate (`2` cases `IH-I4, IH-I5`) = **`2/2` (`100.0%`)**; (5) End-to-end live `Vietnamese Text -> Gemini TypedFactNext` on `46` cases = **`NOT_MEASURED`** (`ALLOW_LIVE_AI=0`). | `RECONCILED` |
| **R-4** | `test_image_crop_retry_dedup.py` test count | Older docs (`CODE_INDEX.md`, `CURRENT_STATE.md`) listed `9 passed` from commit `fb5f9a69` | Commit `32f14b8f` added `test_24_case_synthetic_vision_benchmark_invariants` (`10 passed`). In this release stabilization branch (`b8a9e57b4`), 3 new ingestion correctness regression tests were added, bringing `test_image_crop_retry_dedup.py` to **`13 passed`** (and **`17 passed`** combined with `test_unified_input_20_cases.py`). | `RECONCILED` |
| **R-5** | Active `strict=True` XFAIL inventory | Needed verification that no XFAIL was silently deleted or converted into a pass without architectural support | Verified across the entire backend suite: exactly **`15` `strict=True` XFAILs** remain active (`9` baseline contract XFAILs + `6` capability-boundary XFAILs `G2, G3, G4, G6, G7` in `test_hybrid_reasoning_generalization.py`). Zero XFAILs were removed or weakened. | `RECONCILED` |
| **R-6** | Full backend `pytest` count (`14,031` vs `14,041`) | Previous report at `32f14b8f` recorded `14,031 passed, 7 skipped, 3 deselected, 15 xfailed` | Adding `+7` test items in `test_hybrid_reasoning_generalization.py`, `+3` in `test_image_crop_retry_dedup.py`, and `+1` in `test_independent_holdout_equivalence.py` (`+10` net new passing tests across the full run) brings the authoritative full backend pytest count to **`14,041 passed, 7 skipped, 3 deselected, 15 xfailed, 0 failed`**. | `RECONCILED` |
| **R-7** | `measured_system` in owner approval templates | `test_s2_student_language_pilot_runner.py` checks `k1/r1/s2-owner-approval.template.json` against active `EVALUATION_CANDIDATE.json` | Updated `measured_system` in `docs/evaluation/geometry/runs/hybrid-master-backend-replacement/{k1,r1,s2}-owner-approval.template.json` to `c09b67d538d7d450dc03d8ccaacbb00676241aa4f342d8dbca07bedae974be01` while preserving `approval_status = "TEMPLATE_NOT_APPROVED"`. | `RECONCILED` |

---

## B. Mathematical Correctness Hardening

Machine-readable receipt: [`correctness_hardening_receipt.json`](correctness_hardening_receipt.json) (`SHA-256: c1f5c4019e7a...`).

### 1. Root Cause & Exact Kernel Fix (`backend/app/simulation/geometry_functions/engine.py`)
- Previously, `_Dung.off_base_anchor` tracked only a single secondary off-base height anchor (`z_C > 0` vs `z_C < 0`), so problems containing **two or more independent off-base points** (e.g., two auxiliary apices $P, Q$ at heights $h_1, h_2$ above the base plane $(ABC)$ on the same or opposite sides of $(ABC)$, or an oblique prism with an additional auxiliary apex) could not systematically search all $2^k$ relative half-space sign combinations and verify exact distance/angle constraints (`_kiem_chung_do_dai_goc`).
- **Hardening Implemented**:
  - Replaced the single-anchor field with `off_base_anchors: tuple[str, ...]` (`MAX_SECONDARY_HEIGHT_ANCHORS = 4`) on `_Dung` and recorded every constructed off-base point (`point_from_foot_and_height`, `point_from_equal_slant_edges_and_distance`, `prism_from_oblique_projection`) into `off_base_anchors` while keeping the primary apex canonical (`z > 0`) to quotient global reflection symmetry.
  - Updated `_dao_chieu_cao_off_base(d, anchors_to_flip)` and `dung_tu_loi_goi` to iterate over all non-empty subsets of `off_base_anchors` (`_non_empty_anchor_flips`, up to $2^4 - 1 = 15$ combinations) whenever the default same-side (`z > 0`) placement fails `_kiem_chung_do_dai_goc(d, fg)` or goal evaluation, selecting a sign combination **only if** `_kiem_chung_do_dai_goc(d, fg)` passes with exact arithmetic.
  - If all $2^k$ sign combinations violate `_kiem_chung_do_dai_goc(d, fg)`, the kernel fails closed (`INCONSISTENT_FACTS` / `DEGENERATE_SOLID`) and never emits an unverified coordinate assignment.

### 2. Targeted Mathematical Regressions Added (`backend/tests/geometry/test_hybrid_reasoning_generalization.py`)
All 7 new test executions pass (`35 passed, 6 xfailed` total in `test_hybrid_reasoning_generalization.py`):
1. `test_multi_apex_same_side_vs_opposite_side_disambiguation[same_side]`: Two apices $S$ ($SA = 4$) and $P$ ($PB = 1$) $\perp (ABC)$ with $AB = 4, SP = 5 \implies z_S = +4, z_P = +1$ (same side, $SP^2 = 16 + 9 = 25$).
2. `test_multi_apex_same_side_vs_opposite_side_disambiguation[opposite_side]`: Same setup with $SP = \sqrt{41} \implies z_S = +4, z_P = -1$ (opposite side, $SP^2 = 16 + 25 = 41$).
3. `test_three_independent_off_base_anchors_sign_combination`: Three off-base apices $S, P, Q \perp (ABC)$ requiring the specific sign vector $(+z_S, -z_P, +z_Q)$ to satisfy both $SP = \sqrt{41}$ and $PQ = \sqrt{20} = 2\sqrt{5}$, proving multi-anchor ($2^2 = 4$) sign combination resolution.
4. `test_multi_apex_contradictory_distance_fails_closed`: Impossible cross-apex distance $SP = 7$ fails closed (`status == "refused"`, `error_code == "INCONSISTENT_FACTS"`).
5. `test_equal_slant_edges_impossible_height_exceeding_circumradius_fails_closed`: Pyramid $S.ABC$ with $SA = SB = SC = 2$ over a base of circumradius $R = 5/\sqrt{3} > 2$ ($h^2 = 4 - 25/3 < 0$) fails closed (`DEGENERATE_SOLID`).
6. `test_oblique_prism_impossible_slant_edge_shorter_than_altitude_fails_closed`: Oblique prism with foot $H$, lateral edge $A'A = 2$, and altitude $A'H = 4 > A'A$ fails closed (`DEGENERATE_SOLID`).
7. `test_auxiliary_foot_not_uniquely_determined_fails_closed`: Foot $H$ of $S$ on $(ABC)$ with $SA = 5, SH = 3$ ($AH = 4$) but no placement constraint on $(ABC)$ fails closed (`FOOT_NOT_DETERMINED`) rather than inventing coordinates.

---

## C. Image-Ingestion Correctness Verification

Machine-readable receipt: [`correctness_hardening_receipt.json`](correctness_hardening_receipt.json) (`SHA-256: c1f5c4019e7a...`).

### 1. Audited Edge Cases & Fixes
- **Faint Trailing Line Outside Aggressive Bbox (`backend/app/ingestion/region_detector.py`)**:
  - **Root cause found during audit**: `crop_holds_all_content` checked whether the inner bbox captured $\ge 97\%$ of global ink pixels (`outside_ratio <= 0.03`) and had clean immediate borders. However, on high-resolution pages containing a dense main paragraph plus a **short or faint trailing line** (e.g., `"Tính thể tích khối chóp S.ABCD."` separated by vertical whitespace), that trailing line could account for only $1.5\%\text{–}2.5\%$ of total ink pixels and sit outside the immediate border strip, allowing an aggressive crop to silently drop the goal sentence.
  - **Fix**: Added `_has_faint_ink_outside_bbox(gray, bbox)` to `region_detector.py` and wired it into `crop_holds_all_content`. Using a sensitive adaptive threshold (`C = 8` alongside the standard `C = 15`), it inspects the regions outside `bbox` (`top`, `bottom`, `left`, `right`). If any outside strip contains either $\ge 45$ localized ink pixels or $\ge 3$ rows/columns with horizontal/vertical text-line stroke structure ($\ge 10$ ink pixels per row), `crop_holds_all_content` returns `False`, forcing safe fallback to the full image.
- **Disagreement Preservation Across Fallback (`backend/app/ingestion/unified_input.py`)**:
  - **Root cause found during audit**: When the cropped OCR pass (`primary_ocr`) had low confidence and triggered `full_image_ocr`, if the two passes disagreed on mathematical tokens (`disagreements` non-empty) and `full_image_ocr` had higher confidence, `selected_ocr` switched to `full_image_ocr`. Because `full_image_ocr.low_confidence_tokens` did not include the cross-pass `disagreements`, `needs_confirmation` could evaluate to `False` when `full_image_ocr.confidence >= 0.72`, hiding the token disagreement from the user review UI.
  - **Fix**: Updated `process_image_problem_input` in `unified_input.py` so that whenever `fallback_disagreement` is `True`, all `disagreements` are merged into `selected_ocr.low_confidence_tokens` (capped at 10) and `needs_confirmation` explicitly includes `or fallback_disagreement`, guaranteeing `review_required = True` and preserving both candidate readings in `preprocessing_metadata`.

### 2. Targeted Ingestion Regressions Added (`backend/tests/test_image_crop_retry_dedup.py`)
All 17 tests across `test_image_crop_retry_dedup.py` (13) and `test_unified_input_20_cases.py` (4) pass:
1. `test_crop_holds_all_content_rejects_missing_faint_trailing_line`: Verifies `_has_faint_ink_outside_bbox` and `crop_holds_all_content` reject a crop that cuts off a faint trailing line accounting for $< 2.5\%$ of total ink.
2. `test_fallback_disagreement_forces_review_and_preserves_disagreements_when_full_image_selected`: Verifies that when `full_image_ocr` replaces `primary_ocr` under token disagreement (`"SA = a căn 3"` vs `"SA = a căn 2"`), `needs_confirmation` is `True`, `fallback_disagreement` is `True`, and the differing tokens are preserved in `low_confidence_tokens`.
3. `test_single_shot_gemini_vision_contract_under_retry_and_noisy_border`: Verifies that even when local crop falls back to full image on a noisy border page, Gemini Vision (`extract_raw_from_image`) is called **at most once** (`call_count == 1`).

---

## D. Independent H-1 Validation Readiness

Machine-readable receipt: [`h1_readiness_receipt.json`](h1_readiness_receipt.json) (`SHA-256: d2738677e7f6...`).

- **Validation Status**: **`INDEPENDENT_H1_VALIDATION = NOT_MEASURED`** (`readiness_status = "H1_INFRASTRUCTURE_READY"`).
- **6-Layer Anti-Contamination Scanner (`backend/scripts/score_independent_holdout_equivalence.py`)**:
  Implemented `scan_six_layer_contamination(candidate_text, reference_entries)` and wired it into `build_h1_corpus_integrity_receipt`, checking every candidate H-1 problem against all existing corpora (`72` Dev Matrix cases + `46` Held-Out Geometry cases + historical evaluation corpora = `172` reference cases):
  1. `exact_verbatim`: Byte/whitespace-trimmed verbatim match.
  2. `normalized_text`: Unicode NFC, lowercase, punctuation/whitespace-folded match.
  3. `number_stripped_template`: Structural template match after replacing numeric/variable literals (`2a`, `a\sqrt{3}`, `60^\circ`) with `<NUM>`.
  4. `isomorphic_vertex_renaming`: Order-preserving bijective relabeling of geometric vertices (`S.ABCD` $\leftrightarrow$ `P.MNPQ`, `ABC.A'B'C'` $\leftrightarrow$ `MNP.M'N'P'`) to canonical `<V0>, <V1>, ...`.
  5. `scale_factor_transform`: Normalizes all exact length coefficients by the first positive length in the problem (`SA = 2a, AB = 2a` $\leftrightarrow$ `SA = 5a, AB = 5a`) while preserving angle tokens (`60°`), catching pure homothety/rescaling clones.
  6. `construction_relation_graph`: Order-invariant bag-of-clauses signature over normalized geometric relations ($\perp$, $\parallel$, midpoint, projection, angle, target metric), catching sentence/clause reorderings (`"Cho SA ⊥ (ABCD), gọi M là trung điểm SC"` $\leftrightarrow$ `"Gọi M là trung điểm SC, biết SA ⊥ (ABCD)"`).
- **Verification**: Tested by `test_six_layer_anti_contamination_catches_all_six_probe_types` (`backend/tests/geometry/test_independent_holdout_equivalence.py`), proving all 6 contamination probe types are caught while genuinely distinct problems pass cleanly (`28/28 passed` in `test_independent_holdout_equivalence.py` + `test_paired_live_safe_budget.py`).

---

## E. Real-World Vision Validation Readiness

Machine-readable receipts:
- [`real_world_vision_readiness_receipt.json`](real_world_vision_readiness_receipt.json) (`SHA-256: 18e8bfe005d1...`)
- [`real_world_vision_corpus_template.json`](real_world_vision_corpus_template.json) (`SHA-256: d595bc8decb9...`)

- **Honest Status Classification**:
  - `synthetic_vision_benchmark_24_cases`: **`LOCAL_OCR_DIAGNOSTIC_ONLY`** (proves deterministic preprocessing, crop fallback safety, and single-shot Gemini Vision contract on Pillow-rendered pages; never claimed as real-world camera accuracy or Gemini Vision accuracy).
  - `real_world_camera_corpus`: **`REAL_WORLD_CORPUS_NOT_AVAILABLE`** (no real phone/camera photos exist in the git tree).
  - `live_gemini_vision_evaluation`: **`LIVE_VISION_EVALUATION = NOT_MEASURED`** (`ALLOW_LIVE_AI = 0`).
- **Ready-to-Run Real-World Evaluation Package**:
  - Defined the 7 mandatory real-world capture categories (`printed_textbook_bright`, `Warm_indoor_lighting`, `diagonal_cast_shadow`, `perspective_tilt_trapezoid`, `handwritten_notebook_grid`, `multi_problem_exam_sheet_crop`, `faint_ink_creased_paper`), the 13-token Vietnamese geometry symbol preservation inventory (`⊥`, `∥`, `∠`, `△`, `√`, `°`, `'`, `''`, `S.ABCD`, `ABC.A'B'C'`, `a\sqrt{3}/2`, `d(SA, BC)`, `(SBC)`), and the schema/validator in `reconcile_and_verify_readiness.py::validate_real_world_vision_manifest`.

---

## F. Architecture Gap Decisions (`DEV72-G2, DEV72-G3, DEV72-G4, DEV72-G6, DEV72-G7` / `HB-G2, HB-G4, HB-G6, HB-G7`)

Machine-readable receipt: [`architecture_gap_decisions_receipt.json`](architecture_gap_decisions_receipt.json).

All 6 remaining capability-boundary `strict=True` XFAILs in `backend/tests/geometry/test_hybrid_reasoning_generalization.py` (`PL5, PA3, MG5, SE3, MG9, RE10`, with held-out counterparts `HB35, HB36, HB37, HB38`) were audited across all 10 engineering decision questions and disambiguated from earlier `IH-*` prose labels:

| Gap ID (Dev72 / Held-Out) | XFAIL Case(s) & Pytest Node(s) | Exact Boundary | Affected Modules if Implemented | Mathematical / Verification Risk | Fail-Closed Behavior Today | Decision |
|---|---|---|---|---|---|---|
| **`DEV72-G2` / `HB-G2`** | `PL5`, `PA3` (`test_bridge_level_gap_reproduction[PL5]`, `[PA3]`) · Held-Out: `HB35` | Described point (`@m1`) inside `line` operand of a `distance` goal (`point-to-line` or `line-to-plane`) | `typed_fact_next_bridge.py` (`_resolve_line_2`), `planner.py`, `registry.py` | Requires point-map resolution inside line operands and Source Gate quote grounding for derived-endpoint lines | Fails closed (`BRIDGE_UNSUPPORTED_DESCRIBED_POINT` / `BRIDGE_INVALID_REFERENCE`) | **`DESIGN_ONLY_DEFERRED`** |
| **`DEV72-G3`** | `MG5` (`test_bridge_level_gap_reproduction[MG5]`) | Two described points (`@m1`, `@n1`) referenced simultaneously in a single `distance` goal | `typed_fact_next_bridge.py` (`_lower_math_goal`), `planner.py`, `registry.py` | Requires dual-descriptor source certificate in `registry.py` and ordered prerequisite closure in `planner.py` | Fails closed (`BRIDGE_UNSUPPORTED_DESCRIBED_POINT` / `BRIDGE_INVALID_REFERENCE`) | **`DESIGN_ONLY_DEFERRED`** |
| **`DEV72-G4` / `HB-G4`** | `SE3` (`test_bridge_level_gap_reproduction[SE3]`) · Held-Out: `HB36` | Three-point section plane named `(Q)` in source is lowered to `(MNP)` by `bridge_v2`, losing alias `(Q)` when goal quote asks for `(Q)` | `typed_fact_next_bridge.py` (`_lower_derived_section`), `registry.py` (`mat_cat_dung_nguon`) | Touching `mat_cat_dung_nguon` requires strict quote-anchored plane alias verification so hallucinated plane names remain blocked | Fails closed (`SOURCE_OBJECT_MISMATCH`) | **`DESIGN_ONLY_DEFERRED`** |
| **`DEV72-G6` / `HB-G6`** | `MG9` (`test_g6_three_defined_points_in_one_problem`) · Held-Out: `HB37` | 3+ property-defined points in one problem require ~54 effect candidates and 34 IR memory declarations (`> MAX_EFFECT_CANDIDATES = 48` / `MAX_MEMORY_DECLARATIONS = 32`) | `planner.py` (`MAX_EFFECT_CANDIDATES`), `semantic_program/validator.py` (`MAX_MEMORY_DECLARATIONS`) | Per-goal search without relevance pruning hits `IR_MEMORY_BUDGET_EXCEEDED` (contract ceiling `32`) | Fails closed (`PLAN_TOO_LARGE` / `OUT_OF_SCOPE`) | **`DESIGN_ONLY_DEFERRED`** |
| **`DEV72-G7` / `HB-G7`** | `RE10` (`test_bridge_level_gap_reproduction[RE10]`) · Held-Out: `HB38` | Nested described point (`projection`) defined over a property-defined (`orthocenter`) point | `typed_fact_next_bridge.py` (`_lower_described_point`), `planner.py`, `registry.py` | Depth-2 composition over a locus-defined point (`orthocenter` requires 2 altitudes + intersection) exceeds single-producer `point_tree` certificate | Fails closed (`BRIDGE_UNSUPPORTED_DESCRIBED_POINT` / `BRIDGE_UNSUPPORTED_POINT_CONSTRUCTION`) | **`DESIGN_ONLY_DEFERRED`** |

---

## G. Full T3 Verification & Freeze Integrity

All release candidate verification gates passed with zero failures:

| Verification Gate | Command | Result |
|---|---|---|
| **Full Backend Pytest** | `pytest -q` | **`14,041 passed, 7 skipped, 3 deselected, 15 xfailed, 0 failed`** |
| **Mathematical Generalization Suite** | `pytest tests/geometry/test_hybrid_reasoning_generalization.py -q` | **`35 passed, 6 xfailed, 0 failed`** |
| **Image Ingestion & 24-Case Vision Suite** | `pytest tests/test_image_crop_retry_dedup.py tests/test_unified_input_20_cases.py -q` | **`17 passed, 0 failed`** |
| **H-1 Equivalence & Live-Safe Budget Suite** | `pytest tests/geometry/test_independent_holdout_equivalence.py tests/geometry/test_paired_live_safe_budget.py -q` | **`28 passed, 0 failed`** |
| **Candidate Freeze Verification** | `python scripts/freeze_evaluation_candidate.py --verify` | **`PASS`** (`cay_lam_viec_sach = True`, `product_commit_sha = b8a9e57b4fb13b2ecdba188fbea6f2a76d57caba`, `tree_hash = c09b67d538d7d450dc03d8ccaacbb00676241aa4f342d8dbca07bedae974be01`) |
| **Demo Replay Gate** | `python scripts/replay_demo_cases.py` | **`5/5 PASS`** (`REDUCED_CHAIN_CASES 1/1 PASS`) |
| **Demo Crash Surface Audit** | `python scripts/audit_demo_crash_surface.py` | **`6/6 PASS, 0 thrown`** |
| **Documentation IA Audit** | `python scripts/audit_docs_information_architecture.py` | **`PASS`** (`0 errors`) |
| **Publication Safety Audit** | `python scripts/check_publication_safety.py --range main..HEAD` | **`PASS`** (`0 errors`) |
| **Frontend Vitest Suite** | `npx vitest run` (`npm run test:wave`) | **`136 passed (136)` files, `2000 passed (2000)` tests** |
| **Frontend Production Build** | `npm run build` (`tsc -b && vite build`) | **`PASS`** (`built in 3.94s`) |
| **Full T3 Product Gate** | `node frontend/scripts/full-gate.mjs` | **`FULL_PRODUCT_GATE_PASS` (`5/5` sub-gates green)** |

---

## H. Main Integration Recommendation

- **Recommendation**: **`READY_FOR_MAIN_MERGE_ON_OWNER_APPROVAL`**
- **Summary of Changes on `feat/release-stabilization-validation-readiness`**:
  1. Hardened `Exact Kernel /24` (`engine.py`) to enumerate and verify $2^k$ multi-anchor off-base height sign combinations with exact distance/angle checks (`+7` mathematical tests in `test_hybrid_reasoning_generalization.py`).
  2. Hardened `region_detector.py` (`_has_faint_ink_outside_bbox`) and `unified_input.py` (`fallback_disagreement` preservation & `needs_confirmation` enforcement) so faint trailing lines and cross-pass OCR disagreements are never silently dropped (`+3` regression tests in `test_image_crop_retry_dedup.py`).
  3. Extended `score_independent_holdout_equivalence.py` with 6-layer anti-contamination checking (`exact_verbatim`, `normalized_text`, `number_stripped_template`, `isomorphic_vertex_renaming`, `scale_factor_transform`, `construction_relation_graph`) (`+1` comprehensive probe test in `test_independent_holdout_equivalence.py`).
  4. Reconciled all documentation and evidence metrics across `docs/{CURRENT_STATE,OPEN_ISSUES,CODE_INDEX,EVIDENCE_INDEX}.md`, synced `measured_system` in `k1/r1/s2-owner-approval.template.json`, re-froze `EVALUATION_CANDIDATE.json` on a clean working tree, and generated all 6 machine-readable readiness receipts in `docs/evaluation/geometry/runs/release-stabilization-validation-readiness/`.
- **Branch & Worktree State**:
  - Kept on `feat/release-stabilization-validation-readiness` inside `.superpowers/worktrees/release-stabilization-validation-readiness` per safety rules (`main` untouched, not pushed to `origin`).
