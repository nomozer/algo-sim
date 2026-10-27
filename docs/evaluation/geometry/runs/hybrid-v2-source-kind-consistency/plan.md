# Plan — Hybrid V2 Source Gate `I-1` Consistency Hardening (`hybrid-v2-source-kind-consistency`)

## 0. Authorization & Policy Decision

- **Task**: `HYBRID_V2_SOURCE_GATE_I1_CONSISTENCY_HARDENING`
- **Run ID**: `hybrid-v2-source-kind-consistency`
- **Owner Decision**: `SOURCE_CONTRADICTION_MUST_FAIL_CLOSED`
- **Scope**: Bounded Source Gate (`registry.py`) correction reversing the historical `solid_symbol_outranks_the_solid_word` policy (`I-1`) where the source explicitly states a solid-kind phrase that contradicts the grounded solid identity or verified geometry.
- **Strict Non-Goals**:
  - No merge to `main`, no `git push`, no worktree cleanup.
  - No live provider calls (`ALLOW_LIVE_AI = 0`).
  - No change to `DEFAULT_MODE = LLM_ONLY` or Hybrid opt-in boundary.
  - No change to `Planner /16`, `Engine /14`, `Adapter /4`, `RequestContract`, `TypedFact` bridge, or `CACHE_VERSION = 130` (`NO_BUMP`).

## 1. Baseline & Preflight Verification

- **Branch**: `research/hybrid-v2-planner-generalization`
- **Worktree**: `.superpowers/worktrees/planner-generalization`
- **Reviewed candidate baseline**: `99faf026bdcbcaa2f32e07a9f1687416a820dffd` (documentation HEAD `9b5697bec790645e74c7cec1957af74ba2c5b9fb`)
- **Frozen product baseline**: `37e8435213303f54f37a19b6ce85f896fc0631a0` (`118` files, `tree_hash = 1377e65411c8375cadab093606989c7bff40d47ce5cb7722012fed4300dad305`)
- **RED Baseline Receipts (captured on `99faf026` before product edits)**:
  - `results/red-124-before.json`: `118/124` agree, `6` `fail_open` (the exact 6 `I-1` symbol + contradictory-kind cases), `0` `false_refusal`.
  - `results/red-symbol-before.json`: `16/31` agree, `15` `fail_open`, `0` `false_refusal`.

## 2. Exact Product Change (`Registry /17`)

- Bump `REGISTRY_VERSION` in `backend/app/simulation/geometry_functions/registry.py` from `"geometry-functions/16"` to `"geometry-functions/17"`.
- Enforce both symbol identity AND `_loai_cum_dung` kind compatibility whenever a solid reference contains both a symbol and a kind phrase:
  1. `_khoi_khop`: remove `and not sym and not tu` so `m[n + "k"]` is validated by `_loai_cum_dung` even when `sym` or `tu` is present.
  2. `_cum_goi_khoi`: validate `_loai_cum_dung(cum, solid, calls)` after verifying symbol identity `ky`, rather than early-returning `True` on symbol match alone.
  3. `_mat_hai_duong_dung_nguon`, `mat_cat_dung_nguon`, and `_doc_phep_dung_cau_hoi`: require `_cum_goi_khoi` on matched section phrases.
  4. `_khoi_ro_cum`, `_ten_khoi_khop`, and `_ds_khoi_khop`: validate `_loai_cum_dung` when an explicit kind phrase precedes a solid symbol in `ask_volume_ratio` or `ask_residual_volume`.

## 3. Historical Test Migration & New Test Coverage

- `backend/tests/geometry/test_geometry_library_expansion.py`: pass `kind="hình lập phương"` in `test_projection_waits_for_right_prism_top` so the cube fixture `ABCD.EFGH` asks `"Tính thể tích hình lập phương ABCD.EFGH."` instead of `"Tính thể tích hình chóp ABCD.EFGH."`.
- `backend/tests/geometry/test_hybrid_ask_operand_binding.py`:
  - Update `test_solid_symbol_outranks_the_solid_word` to assert the amended Owner policy (`SOURCE_CONTRADICTION_MUST_FAIL_CLOSED`), referencing `decision-amendment.md`.
  - Update `MUTANTS` string target for the `/17` `_khoi_khop` check.
- `backend/tests/geometry/test_solid_kind_source_binding.py`:
  - Remove `@pytest.mark.xfail(strict=True)` from `test_correct_symbol_with_contradicting_kind_word_is_still_served` and rename/expand it to cover all symbol + compatible/contradictory kind combinations (`Ask_volume`, `Section`, `Ask_section_area`, multi-solid isolation, fact-order permutation, `4x4x4` cuboid without cube premise).

## 4. Verification & Freeze Gates

1. `results/green-124-after.json`: `124/124` agree (`0` `fail_open`, `0` `false_refusal`).
2. `results/green-symbol-after.json`: `31/31` agree (`0` `fail_open`, `0` `false_refusal`).
3. `results/development-regression-registry17.json`: `10/10` positives (`10/10` oracle match), `8/8` negatives, `0` wrong-served.
4. Freeze new candidate (`EVALUATION_CANDIDATE.json`) and declare `candidate_divergence.json` (`NO_BUMP` on `CACHE_VERSION = 130`).
5. Run T0 (`impact.mjs --base main`), T1 (`tests/geometry` + `tests/semantic_program`), T2 (`vitest`), and Full T3 (`full-gate.mjs` on clean detached checkout of the frozen candidate), followed by post-T3 `freeze_evaluation_candidate.py --verify` (`MATCH`).
6. Independent read-only review (`review.md`) and final documentation sync (`report.md`, `handoff.md`, `run.json`, `docs/CODE_INDEX.md`, `docs/CURRENT_STATE.md`, `docs/AI_CONTEXT_BUNDLE.md`, `docs/ROADMAP.md`).
