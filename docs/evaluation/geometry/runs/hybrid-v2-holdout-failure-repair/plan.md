# Implementation Plan — Hybrid V2 Holdout Failure Repair (`HYBRID_V2_HOLDOUT_FAILURE_REPAIR`)

## 1. Mission & Scope

- **Task**: `HYBRID_V2_HOLDOUT_FAILURE_REPAIR`
- **Baseline**: `129c1a952393808bfcdb6ecb48677c09b2ed6293` (`main = origin/main`)
- **Worktree**: `.superpowers/worktrees/holdout-failure-repair` on branch `research/hybrid-v2-holdout-failure-repair`
- **Preserved Holdout Worktree**: `.superpowers/worktrees/independent-section-holdout` on branch `research/hybrid-v2-independent-vietnamese-section-holdout` (`f7f177a626c33bb13aa40d3a904c82266ed8a276`) — read-only, untouched.
- **Authorization**:
  1. Reconcile the prose summary vs. frozen holdout evidence (`results/scored-run-1/summary.json`, `results/scored-run-1/track-a.json`, `results/analysis.json`, `review.md`).
  2. Reclassify the opened 84-case holdout as `POST_FEEDBACK_DEVELOPMENT_REGRESSION` and author a new independent development corpus (`inputs/new-development-corpus.json`) + independent exact `Fraction` oracle (`oracle/new_dev_oracle.py`) + pytest suite (`backend/tests/geometry/test_holdout_failure_repair.py`) before editing product code (RED → GREEN).
  3. Implement bounded correctness and language-coverage repairs **M1–M5** in one commit:
     - **Phase A (M1)**: Consistent plane identifier validation (`PlaneName` accepting Latin `[A-Z][0-9]*'?` and Greek `[α-ω]'?` while preserving `TypedFact.model_json_schema()` compatibility) and `MAT_HAI_DUONG` / `_kiem_nguon_dong` Source Gate parity with `MAT_SONG_SONG` and `MAT_VUONG_DUONG`.
     - **Phase B (M2)**: Deterministic single-solid resolution for omitted `solid` on `height` and `altitude` facts when and only when a unique root solid exists and agrees with source ownership, plus plural quantifier `(các|mọi|mỗi)` support in SG-3 role-value grammar (`_C_VAI`, `_C_DAY`, `_C_NOI`).
     - **Phase C (M3)**: Bounded Source Gate section wording expansion (`khi (bị )?cắt bởi`, `thiết diện tạo bởi <khối> và mặt phẳng (...)`, named section polygon `thiết diện <POLY>`, 4-vertex coplanar solid reference planes in `mat_song_song_dung_nguon`, inline section prefix matching on full `de`, `đường chéo / cạnh bên / đoạn thẳng` in `_QUA_VUONG_DUONG`, and `Tính theo a ...` in `_GIUA_HOP_LE` / `_kiem_don_vi_hoi`).
     - **Phase D (M4)**: Bounded compound premise coverage in `registry.py` (unlabelled `đáy` before `là` when owned by the immediately preceding solid symbol via `_chu_cua_day`, `trùng với` in `orthogonal_projection`, `các kích thước` before segment labels, and `tam giác <POLY> vuông (cân) tại <V>` in `_C_DAY` / `_cau_tien_de_dong_hop_le`).
     - **Phase E (M5)**: Bounded section-area question reference resolution across Bridge, Planner, and Source Gate for anaphoric `"tính diện tích của nó"` (unique section antecedent) and `"tính diện tích (tam giác|tứ giác|đa giác) <POLY>"` when `<POLY>` matches the grounded section polygon (`{through_point, *cut_points}`).
  4. Implement **Phase F (R2)** in a **separate commit** after M1–M5:
     - Prevent internal plane-construction auxiliary labels (`H`, `H1..H4` from `MAT_SONG_SONG`, `MAT_HAI_DUONG`, `MAT_VUONG_DUONG`, `DINH_CAT_CANH`) from leaking as source-like `notation` or narration tokens in Scene3D while preserving source-mentioned `H` and dependency/formation integrity.
  5. Run post-feedback comparison on the frozen 84 cases (`results/post-feedback-84-comparison.json`, labelled `POST_FEEDBACK_REGRESSION_NOT_INDEPENDENT_HOLDOUT`), execute T0/T1/T2/Full T3 gates, freeze the candidate, run an independent read-only code review subagent (`review.md`), and complete all run documentation.

## 2. Step-by-Step Execution Sequence

1. **Preflight & Evidence Reconciliation** (`baseline-audit.md`)
2. **Architecture Decision Record** (`architecture-decision.md`)
3. **New Development Corpus & Independent Oracle Registration + RED Evaluation** (`inputs/new-development-corpus.json`, `oracle/new_dev_oracle.py`, `backend/tests/geometry/test_holdout_failure_repair.py`, `results/red-evaluation.json`)
4. **M1–M5 Implementation & Separate Commit** (`typed_fact_next_bridge.py`, `planner.py`, `registry.py`, version pin updates)
5. **R2 Scene3D Label Hygiene Implementation & Separate Commit** (`function_route.py`, `test_section_display_identity.py`, `test_typedfactnext_planner_bridge.py`, `results/green-evaluation.json`)
6. **Post-Feedback 84-Case Diagnostic Comparison** (`results/post-feedback-84-comparison.json`)
7. **Verification Gates (T0, T1, T2, Freeze, Detached Full T3, Post-T3 Freeze Match) & Independent Review (`review.md`)**
8. **Final Run Artifacts & Living Documentation Updates** (`report.md`, `handoff.md`, `run.json`, `candidate_divergence.json`, canonical docs)
