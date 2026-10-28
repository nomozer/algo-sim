# Implementation Plan — `HYBRID_V2_W3_F1_CROSS_SENTENCE_PLANE_GROUNDING`

## 1. Mission & Scope

- **Task ID:** `HYBRID_V2_W3_F1_CROSS_SENTENCE_PLANE_GROUNDING`
- **Classification:** Product repair wave (`W3-F1: SECTION_AND_AREA_COMPOUND_QUESTION_GROUNDING`)
- **Authoritative Baseline (`main = origin/main`):** `e137623c4f674135a8d7884b78614c132eb78085`
- **Baseline Product Commit:** `73ca8d92e74059680ce53b99692af396df37a2f8`
- **Baseline Product Freeze (`118` files):** `1170ca163529dd40b57f4058826db92a6433359546aa2ad718712f38a538c10d`
- **Research Branch:** `research/hybrid-v2-w3-f1-cross-sentence-plane-grounding`
- **Research Worktree:** `.superpowers/worktrees/w3-f1-cross-sentence-plane-grounding`
- **Evidence Package:** `docs/evaluation/geometry/runs/hybrid-v2-w3-f1-cross-sentence-plane-grounding/`

### Strict Scope Boundaries

1. **In Scope:** Repair **only `W3-F1`** — Grounded Cross-Sentence Plane Reference Resolution and standalone/compound-question plane grounding across sentences (`_QUA_SONG_SONG`, `_DIEM_TRUOC_SONG_SONG`, `_QUA_VUONG_DUONG`, `_DIEM_TRUOC_VUONG_DUONG`, `_QUA_HAI_DUONG`, `_DIEM_TRUOC_HAI_DUONG`, `_CUM_DUNG_MAT_PHU`, `mat_song_song_dung_nguon`, `_kiem_vung_tien_de`, `_kiem_du_kien_cau_hoi`, and consistent `plane_name` propagation across all three plane relations in `typed_fact_next_bridge.py`, `planner.py`, and `registry.py`).
2. **Out of Scope (Strictly Forbidden in This Wave):**
   - `W3-F2` — `divide_segment` (`"thỏa mãn"` / `"với"`) and `orthogonal_projection` (`"chân đường cao"`) lexicon
   - `W3-F3` — `parallel_two_lines` `_kiem_nguon_dong` (`_cau_tien_de_dong_hop_le`) premise grammar
   - `W3-F4` — `cube` edge-length binding via base-square sentence
   - `W3-F5` — `"Giả sử"` conditional substring false positive
   - New solid families, DSL, OCR, multi-object geometry, or production default routing (`DEFAULT_MODE = LLM_ONLY` remains unchanged).
3. **Preservation of Historical Holdout Wave 3:**
   - Branch `research/hybrid-v2-independent-vietnamese-geometry-holdout-wave3` in `.superpowers/worktrees/independent-section-holdout-wave3` (`0943f0ee6bd2a2b297827e39fa7c07054d716ea9`) and its `results/scored-run-1/` remain 100% untouched.
   - Any replay of the locked 144-case Wave 3 corpus is classified strictly as `POST_FEEDBACK_DEVELOPMENT_REGRESSION`.

---

## 2. Step-by-Step Execution Sequence

1. **Step 1 — Baseline Audit, Preregistration & RED Reproduction (`results/red-before.json`):**
   - Audit all 24 historical `W3-F1` cases from Wave 3 (`baseline-audit.md`).
   - Document the architectural design of **Grounded Cross-Sentence Plane Reference Resolution** (`architecture-decision.md`).
   - Preregister `inputs/development.json` and `inputs/oracle.json`:
     - **Slice A (`historical_w3_f1_verbatim`, 24 cases):** Exact verbatim 24 `W3-F1` cases from Wave 3 (`18` Category B, `6` Category A), documenting the `9` pure-`W3-F1` cases and the `15` multi-defect cases (`W3-F1` + masked secondary `W3-F2`/`W3-F3`/`W3-F4` premise defect).
     - **Slice B (`w3_f1_isolated_24`, 24 cases):** All 24 Wave 3 `W3-F1` geometric problems with non-plane premise wording normalized to Registry `/19`-supported premise wording so `W3-F1` is evaluated in isolation across all 24 configurations (`18` Category B, `6` Category A).
     - **Slice C (`authored_cross_sentence_positive`, 24 cases):** Newly authored positive cases covering same-sentence vs two-sentence (`derived_section.quote` on definition vs on question-only) vs multi-intermediate-sentence vs renamed planes (`(P)`, `(Q)`, `(R)`, `(α)`, `(β)`, `(γ)`) vs reordered premises vs `section_only` / `area_only` / `section_and_area` vs Category A & B across all 6 supported solid families.
     - **Slice D (`mandatory_negative_tamper`, 20 cases):** All 20 mandatory adversarial/tamper classes from Owner GO §7.
   - Run `tools/build_and_evaluate_w3_f1.py --mode red` on unmodified baseline (`geometry-functions/19`) to produce `results/red-before.json` and commit preregistration before touching product code.

2. **Step 2 — Product Implementation (`W3-F1` Only) & Adversarial Unit Tests:**
   - Implement Grounded Cross-Sentence Plane Reference Resolution in `backend/app/simulation/geometry_functions/registry.py`, `backend/app/simulation/geometry_functions/planner.py`, and `backend/app/simulation/geometry_functions/typed_fact_next_bridge.py`.
   - Bump `REGISTRY_VERSION` to `"geometry-functions/20"` and `PLANNER_VERSION` to `"geometry-fact-planner/18"` (recording the delta in `backend/scripts/export_hybrid_preview_fixtures.py` and version-pinned tests) while preserving `CACHE_VERSION = "130"` and `DEFAULT_MODE = "LLM_ONLY"`.
   - Add `backend/tests/geometry/test_w3_f1_cross_sentence_plane_grounding.py` covering all positive variations and all 20 mandatory negative/tamper classes.

3. **Step 3 — GREEN Evaluation, Locked Wave 3 Post-Feedback Regression & Mandatory Regressions:**
   - Run `tools/build_and_evaluate_w3_f1.py --mode green` to generate `results/green-after.json` and `results/wave3-post-feedback-regression.json` (`POST_FEEDBACK_DEVELOPMENT_REGRESSION`).
   - Run all mandatory offline regression suites (`ALLOW_LIVE_AI=0`).

4. **Step 4 — Candidate Freeze, Authoritative Full T3 on Detached Worktree & Independent Review:**
   - Update candidate freeze (`scripts/freeze_evaluation_candidate.py`), commit product & test changes, and execute Full T3 on a clean detached worktree at the frozen candidate commit.
   - Record `verification/tiers.json` and `full-t3/receipt.json`.
   - Run Independent Reviewer subagent (`review.md`) across all 10 mandatory review dimensions (Owner GO §12).
   - Write `report.md`, `handoff.md`, `run.json`, update living docs, verify docs IA and publication safety, and stop at `READY_FOR_OWNER_REVIEW`.
